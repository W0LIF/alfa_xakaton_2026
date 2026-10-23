import argparse
import json
import random
from pathlib import Path

import pandas as pd


ORG_TYPES = ["ООО", "АО", "ПАО"]
OKFS_NAMES = ["Частная собственность", "Государственная собственность", "Смешанная"]
COMPANY_AGE = ["до 1 года", "1–3", "3–5", "5–10", "более 10"]
ECO_MARKS = ["Старт", "Рост", "Зрелость", "Спад"]
WORKERS = ["до 15", "15–50", "50–250", "250–500", "более 500"]
CL_TYPES = ["Действующий клиент", "Потенциальный клиент"]
def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_catalogs()->dict:
    base = Path(__file__).parent / "catalogs"
    return {
        "okved": load_json(base / "okved.json"),
        "geo": load_json(base / "geo.json"),
        "countries": load_json(base / "countries.json"),
    } 
def _sector(okved_name: str, catalogs: dict) -> str:
    for item in catalogs["okved"]:
        if item["name"] == okved_name:
            return item["sector"]
    return "Прочее"
def make_companies(n: int, catalogs: dict) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        okved = random.choice(catalogs["okved"])
        geo = random.choice(catalogs["geo"])
        revenue = random.randint(15_000_000_000, 500_000_000_000)

        row = {
            "SYNTHETIC_U": f"U_{i:06d}",
            "ORG_TYPE": random.choice(ORG_TYPES),
            "OKFS_NAME": random.choice(OKFS_NAMES),
            "COMPANY_AGE_YEARS_GRADATION": random.choice(COMPANY_AGE),
            "ECO_MARK_LABEL": random.choice(ECO_MARKS),
            "MAINOKVED_CODE": okved["code"],
            "MAINOKVED_NAME": okved["name"],
            "NEGATIVEMARK": 1 if random.random() < 0.07 else 0,
            "AMOUNT_WORKERS_FNS_GRADATION": random.choice(WORKERS),
            "AMOUNT_WORKERS_SPARK_GRADATION": random.choice(WORKERS),
            "CL_TYPE": random.choice(CL_TYPES),
            "CL_PRODUCT_RKO_MARK": 1 if random.random() < 0.80 else 0,
            "CL_PRODUCT_GAR_MARK": 1 if random.random() < 0.20 else 0,
            "CL_PRODUCT_LOA_MARK": 1 if random.random() < 0.40 else 0,
            "CL_PRODUCT_LEA_MARK": 1 if random.random() < 0.25 else 0,
            "CL_PRODUCT_DEP_MARK": 1 if random.random() < 0.45 else 0,
            "CL_PRODUCT_ZPP_MARK": 1 if random.random() < 0.50 else 0,
            "FTS_FLAG": None,
            "FTS_COUNTRY_NAME": None,
            "FACTORING_MARK": 1 if random.random() < 0.10 else 0,
            "REVENUE_COMPANY": revenue,
            "GROUP_ID": None,
            "CITY": geo["city"],
            "REGION": geo["region"],
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    high_fts_sectors = {"Логистика", "Оптовая торговля", "Производство", "Добыча", "Химия", "Машиностроение"}
    df["FTS_FLAG"] = df["MAINOKVED_NAME"].map(
        lambda name: 1 if _sector(name, catalogs) in high_fts_sectors and random.random() < 0.55 else 0
    )
    
    mask = df["FTS_FLAG"] == 1
    df.loc[mask, "FTS_COUNTRY_NAME"] = [
        random.choice(catalogs["countries"]) for _ in range(mask.sum())
    ]

    return df

def assign_groups(df:pd.DataFrame, n_groups:int)->pd.DataFrame:
    n_in_groups = int(len(df)*0.6)
    indices_in_groups = random.sample(range(len(df)), n_in_groups)
    group_names = [f"G_{i+1:03d}" for i in range(n_groups)]
    for idx in indices_in_groups:
        df.at[idx, "GROUP_ID"] = random.choice(group_names)
        
    return df

def make_links(companies: pd.DataFrame, catalogs: dict) -> pd.DataFrame:
    rows = []
    person_id_counter = 1

    company_persons = {uid: [] for uid in companies["SYNTHETIC_U"]}

    company_person = {uid:[] for uid in companies["SYNTHETIC_U"]}
    for _,company in companies.iterrows():
        uid = company["SYNTHETIC_U"]
        city = company["CITY"]
        region = company["REGION"]

        num_persons = random.randint(1,3)
        
        for _ in range(num_persons):
            fid = f"F_{person_id_counter:06d}"
            person_id_counter += 1

            if random.random() < 0.8:
                p_city, p_region = city, region
            else:
                geo = random.choice(catalogs["geo"])
                p_city, p_region = geo["city"], geo["region"]

            rows.append({
                "SYNTHETIC_F": fid,
                "SYNTHETIC_U": uid,
                "CITY_NAME": p_city,
                "RC_NAME": p_region
            })
            
            company_persons[uid].append(fid)

    num_links = int(len(rows) * 0.08) 

    for _ in range(num_links):
       
        uid1, uid2 = random.sample(list(company_persons.keys()), 2)
       
        if not company_persons[uid1]:
            continue
        fid = random.choice(company_persons[uid1])
 
        company2 = companies[companies["SYNTHETIC_U"] == uid2].iloc[0]
        
        rows.append({
            "SYNTHETIC_F": fid,
            "SYNTHETIC_U": uid2,
            "CITY_NAME": company2["CITY"],
            "RC_NAME": company2["REGION"]
        })

    return pd.DataFrame(rows)

def make_payments(companies: pd.DataFrame)-> pd.DataFrame:
    rows = []
    uids = companies["SYNTHETIC_U"].tolist()

    num_concentrated = int(len(uids)*0.15)
    concentrated_uids = random.sample(uids, num_concentrated)

    for payer in uids:
        
        num_beneficiaries = random.randint(3, 10)
        
        
        possible_beneficiaries = [u for u in uids if u != payer]
        beneficiaries = random.sample(possible_beneficiaries, num_beneficiaries)
        
        for i, beneficiary in enumerate(beneficiaries):
            
            if payer in concentrated_uids and i == 0:
                pay_amt = random.randint(500_000_000, 1_000_000_000)
                pay_cnt = random.randint(200, 500)
            else:
                pay_amt = random.randint(1_000_000, 100_000_000)
                pay_cnt = random.randint(1, 50)

            rows.append({
                "PAYER": payer,
                "BENEFICIARY": beneficiary,
                "PAY_AMT": pay_amt,
                "PAY_CNT": pay_cnt
            })

    return pd.DataFrame(rows)

def setup_demo_clients(companies: pd.DataFrame, catalogs: dict) -> dict:
    # Найдем индексы для A, B и C (возьмем просто первые попавшиеся компании)
    idx_a = companies.index[0]
    idx_b = companies.index[1]
    idx_c = companies.index[2]

    # --- КЛИЕНТ А: Зависит от ставки (производство + кредиты) ---
    companies.at[idx_a, "MAINOKVED_NAME"] = "Производство двигателей и турбин"
    companies.at[idx_a, "MAINOKVED_CODE"] = "28.11"
    companies.at[idx_a, "CL_PRODUCT_LOA_MARK"] = 1
    companies.at[idx_a, "CL_PRODUCT_LEA_MARK"] = 1
    companies.at[idx_a, "FTS_FLAG"] = 0
    companies.at[idx_a, "FTS_COUNTRY_NAME"] = None
    companies.at[idx_a, "REVENUE_COMPANY"] = 150_000_000_000

    # --- КЛИЕНТ Б: Экспортёр (логистика + ФТС Китай) ---
    companies.at[idx_b, "MAINOKVED_NAME"] = "Деятельность автомобильного грузового транспорта"
    companies.at[idx_b, "MAINOKVED_CODE"] = "49.41"
    companies.at[idx_b, "FTS_FLAG"] = 1
    companies.at[idx_b, "FTS_COUNTRY_NAME"] = "Китай"
    companies.at[idx_b, "CL_PRODUCT_LOA_MARK"] = 0
    companies.at[idx_b, "REVENUE_COMPANY"] = 80_000_000_000

    # --- КЛИЕНТ В: Логистика/Ритейл (много контрагентов, без кредитов) ---
    companies.at[idx_c, "MAINOKVED_NAME"] = "Торговля оптовая неспециализированная"
    companies.at[idx_c, "MAINOKVED_CODE"] = "46.90"
    companies.at[idx_c, "FTS_FLAG"] = 0
    companies.at[idx_c, "CL_PRODUCT_LOA_MARK"] = 0
    companies.at[idx_c, "REVENUE_COMPANY"] = 45_000_000_000

    # Возвращаем словарь с ID для сохранения в JSON
    return {
        "A": {"client_id": companies.at[idx_a, "SYNTHETIC_U"], "scenario": "interest_rate"},
        "B": {"client_id": companies.at[idx_b, "SYNTHETIC_U"], "scenario": "fx_export"},
        "C": {"client_id": companies.at[idx_c, "SYNTHETIC_U"], "scenario": "logistics"},
    }

def main() -> None:
    parser =  argparse.ArgumentParser(description="Генерация датасета")
    parser.add_argument("--out", default="backend/data/raw", help="Куда сохранять CSV")
    parser.add_argument("--seed", default=42, help="Seed для воспроизводиости")
    parser.add_argument("--n-companies", default=400, type=int, help="Сколько компаний")
    parser.add_argument("--n-groups", default=40, type=int, help="Сколько групп")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)  

    print(f"Генерация: seed={args.seed}")
    print(f"Куда сохранять: {out_dir}")

    
    catalogs = load_catalogs()
    print(f"Справочники: ОКВЭД {len(catalogs['okved'])}, городов {len(catalogs['geo'])}, стран {len(catalogs['countries'])}")

    companies = make_companies(args.n_companies, catalogs)
    companies = assign_groups(companies, args.n_groups)

        # Настраиваем демо-клиентов A, B, C
    demo_clients = setup_demo_clients(companies, catalogs)
    
    # Сохраняем их ID в processed/demo_clients.json
    processed_dir = Path("backend/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    with open(processed_dir / "demo_clients.json", "w", encoding="utf-8") as f:
        json.dump(demo_clients, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: {processed_dir / 'demo_clients.json'} (демо-клиенты A, B, C)")
    
    companies_path = out_dir / "df_Uid_data_hack.csv"
    companies.to_csv(companies_path, index=False, encoding="utf-8-sig")
    print(f"Сохранено: {companies_path} ({len(companies)} строк)")

    links = make_links(companies, catalogs)
    links_path = out_dir / "df_Fid_Uid_link_hack.csv"
    links.to_csv(links_path, index=False, encoding="utf-8-sig")
    print(f"Сохранено: {links_path} ({len(links)} строк)")

    payments = make_payments(companies)
    payments_path = out_dir / "df_Uid_payment_hack.csv"
    payments.to_csv(payments_path, index=False, encoding="utf-8-sig")
    print(f"Сохранено: {payments_path} ({len(payments)} строк)")



if __name__ == "__main__":
    main()