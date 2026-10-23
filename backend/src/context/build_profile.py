import json
from pathlib import Path
import pandas as pd

def load_data():
    """Загружает все три датасета."""
    base_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
    
    companies = pd.read_csv(base_dir / "df_Uid_data_hack.csv")
    links = pd.read_csv(base_dir / "df_Fid_Uid_link_hack.csv")
    payments = pd.read_csv(base_dir / "df_Uid_payment_hack.csv")
    
    return companies, links, payments


def build_profile(client_id: str) -> dict:
    """Собирает профиль клиента по его ID (SYNTHETIC_U)."""
    companies, links, payments = load_data()
    
    # 1. Находим компанию
    company_row = companies[companies["SYNTHETIC_U"] == client_id]
    if company_row.empty:
        raise ValueError(f"Компания с ID {client_id} не найдена")
    
    company = company_row.iloc[0]
    
    # 2. Собираем базовую информацию
    profile = {
        "client_id": client_id,
        "group_id": company["GROUP_ID"] if pd.notna(company["GROUP_ID"]) else None,
        "industry": {
            "okved_code": str(company["MAINOKVED_CODE"]),
            "okved_name": company["MAINOKVED_NAME"],
            "sector": company["MAINOKVED_NAME"], # Упрощенно берем название как сектор
        },
        "scale": {
            "revenue": int(company["REVENUE_COMPANY"]),
            "workers_gradation_fns": company["AMOUNT_WORKERS_FNS_GRADATION"],
            "company_age": company["COMPANY_AGE_YEARS_GRADATION"],
            "stage": company["ECO_MARK_LABEL"],
            "region": company["REGION"],
            "city": company["CITY"],
        },
        "banking_products": {
            "rko": bool(company["CL_PRODUCT_RKO_MARK"]),
            "loans": bool(company["CL_PRODUCT_LOA_MARK"]),
            "leasing": bool(company["CL_PRODUCT_LEA_MARK"]),
            "deposits": bool(company["CL_PRODUCT_DEP_MARK"]),
            "guarantees": bool(company["CL_PRODUCT_GAR_MARK"]),
            "payroll": bool(company["CL_PRODUCT_ZPP_MARK"]),
            "factoring": bool(company["FACTORING_MARK"]),
        },
        "foreign_trade": {
            "fts_flag": bool(company["FTS_FLAG"]),
            "countries": [company["FTS_COUNTRY_NAME"]] if pd.notna(company["FTS_COUNTRY_NAME"]) else [],
        },
        "risk_flags": {
            "negative_mark": bool(company["NEGATIVEMARK"]),
        },
    }

    # 3. Анализируем связи (физлица)
    company_links = links[links["SYNTHETIC_U"] == client_id]
    profile["relations"] = {
        "linked_persons_count": len(company_links),
        "linked_person_ids": company_links["SYNTHETIC_F"].tolist(),
    }

    # 4. Анализируем платежи (контрагенты)
    # Ищем, кому платила компания, и кто платил ей
    out_payments = payments[payments["PAYER"] == client_id]
    in_payments = payments[payments["BENEFICIARY"] == client_id]
    
    # Считаем общий объем
    total_out = out_payments["PAY_AMT"].sum()
    
    # Ищем главного контрагента (риск концентрации)
    if not out_payments.empty:
        top_contractor = out_payments.sort_values(by="PAY_AMT", ascending=False).iloc[0]
        top_contractor_id = top_contractor["BENEFICIARY"]
        top_contractor_share = top_contractor["PAY_AMT"] / total_out if total_out > 0 else 0
    else:
        top_contractor_id = None
        top_contractor_share = 0.0

    profile["relations"]["payment_volume_total"] = int(total_out)
    profile["relations"]["top_counterparty"] = top_contractor_id
    profile["relations"]["top_counterparty_share"] = round(top_contractor_share, 2)

    # 5. Выставляем веса для ранжирования (personalization_weights)
    # Логика: если есть кредиты -> ставка важна. Если есть ФТС -> валюта важна.
    weights = {
        "interest_rate": 0.1,
        "logistics": 0.1,
        "regulation": 0.1,
        "fx": 0.1,
        "commodities": 0.1
    }

    # Повышаем вес ставки, если есть кредиты или лизинг
    if profile["banking_products"]["loans"]:
        weights["interest_rate"] += 0.5
    if profile["banking_products"]["leasing"]:
        weights["interest_rate"] += 0.2
        
    # Повышаем вес валюты, если есть внешняя торговля
    if profile["foreign_trade"]["fts_flag"]:
        weights["fx"] += 0.5
        
    # Повышаем вес логистики, если отрасль - логистика (упрощенно по названию)
    if "транспорт" in profile["industry"]["okved_name"].lower() or "торговля" in profile["industry"]["okved_name"].lower():
        weights["logistics"] += 0.4
        
    # Риск концентрации повышает важность новостей про контрагентов (регулирование/риски)
    if top_contractor_share > 0.5:
        weights["regulation"] += 0.3

    # Нормализуем веса (чтобы сумма была 1.0)
    total_weight = sum(weights.values())
    for k in weights:
        weights[k] = round(weights[k] / total_weight, 2)

    profile["personalization_weights"] = weights

    return profile


if __name__ == "__main__":
    # Тестируем на демо-клиенте A
    processed_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
    
    try:
        with open(processed_dir / "demo_clients.json", "r", encoding="utf-8") as f:
            demo = json.load(f)
            client_id = demo["A"]["client_id"]
            
        print(f"Строим профиль для клиента A ({client_id})...")
        result = build_profile(client_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except FileNotFoundError:
        print("Ошибка: файл demo_clients.json не найден. Сначала запустите generate_synthetic.py")