import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey, Table, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

load_dotenv()

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

#1 - python translating to sql (this below is hardcode, the above is using db)
# engine = create_engine('postgresql+psycopg2://postgres:Jehovah777!@Localhost:5432/construction_db', echo=True)
# SessionLocal = sessionmaker(bind=engine)
# Base = declarative_base()

#2 - DDL

# M:N junction table
machine_mechanics = Table(
    'machine_mechanics', Base.metadata,
    Column('equipment_id', Integer, ForeignKey('heavy_equipment.equipment_id'), primary_key=True),
    Column('mechanic_id', Integer, ForeignKey('mechanics.mechanic_id'), primary_key=True),
)

class HeavyEquipment(Base):
    __tablename__ = 'heavy_equipment'
    equipment_id = Column(Integer, primary_key=True)
    machine_name = Column(String(100), nullable=False)
    machine_type = Column(String(50))
    maintenance_records = relationship("MaintenanceLog", back_populates="machine") # 1:N
    mechanics = relationship("Mechanic", secondary=machine_mechanics, back_populates="machines") # M:N

class Mechanic(Base):
    __tablename__ = 'mechanics'
    mechanic_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    machines = relationship("HeavyEquipment", secondary=machine_mechanics, back_populates="mechanics") # M:N

class MaintenanceLog(Base):
    __tablename__ = 'maintenance_logs'
    log_id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    cost = Column(Numeric(10, 2))
    equipment_id = Column(Integer, ForeignKey('heavy_equipment.equipment_id'))
    machine = relationship("HeavyEquipment", back_populates="maintenance_records")

##destroy all old tables
Base.metadata.drop_all(engine)

#create
Base.metadata.create_all(engine)


#3 - DML
db = SessionLocal()

if db.query(HeavyEquipment).count() == 0:
    print("\n--- Inserting new Data ---")

# Parents
excavator = HeavyEquipment(machine_name="CAT-320", machine_type="Excavator")
bulldozer = HeavyEquipment(machine_name="Komatsu-D39", machine_type="Bulldozer")

# Children
log_1 = MaintenanceLog(description="Replaced hydraulic hose", cost=1500.00, machine=excavator)
log_2 = MaintenanceLog(description="Routine oil change", cost=450.00, machine=excavator)
log_3 = MaintenanceLog(description="Routine oil change", cost=450.00, machine=excavator)

# M:N mechanics entities
mutu = Mechanic(name="Mutu")
ah_chong = Mechanic(name="Ah Chong")

excavator.mechanics.extend([mutu, ah_chong]) # both work on it
bulldozer.mechanics.append(mutu) # only mutu

db.add_all([excavator, bulldozer, log_1, log_2, log_3, mutu, ah_chong])
db.commit()
print("Data uploaded to PostgreSQL")


#4 - DQL
#INNER JOIN
results = db.query(HeavyEquipment.machine_name, MaintenanceLog.description, MaintenanceLog.cost).join(MaintenanceLog).all()
for name, desc, cost in results:
    print(f"{name:<15} | {desc:<25} | RM {cost}")

#IS NULL
missing_logs = db.query(HeavyEquipment.machine_name).outerjoin(MaintenanceLog).filter(MaintenanceLog.log_id.is_(None)).all()
for machine in missing_logs:
    print(f"- {machine[0]} has zero logs.")


# M:N
all_machines = db.query(HeavyEquipment).all()
for machine in all_machines:
    mechanic_names = [m.name for m in machine.mechanics]
    print(f"Machine: {machine.machine_name:<15} | Assigned Mechanics: {', '.join(mechanic_names)}")

# Aggregations SUM
total_costs = db.query(
    HeavyEquipment.machine_name,
    func.sum(MaintenanceLog.cost).label('total')
).join(MaintenanceLog).group_by(HeavyEquipment.machine_name).all()

for machine_name, total in total_costs:
    print(f"{machine_name} Total Maintenance Cost: RM {total:,.2f}")

# Subqueries (Queries inside Queries)
print("Find specific repairs that cost MORE than the average repair.\n")
avg_repair_cost = db.query(func.avg(MaintenanceLog.cost)).scalar_subquery()
expensive_logs = db.query(
    HeavyEquipment.machine_name,
    MaintenanceLog.description,
    MaintenanceLog.cost
).join(MaintenanceLog).filter(
    MaintenanceLog.cost > avg_repair_cost
).all()

for name, desc, cost in expensive_logs:
    print(f"EXPENSIVE REPAIR DETECTED: {name} - {desc} RM {cost:,.2f}")

db.close()

#5 - API

print("\n-- Connecting to fake API---")

weather_api_key = os.getenv("SARAWAK_WEATHER_API")

#safety check

if not weather_api_key:
    print("Error, the key is missing")
else:
    masked_key = f"{weather_api_key[:10]}...{weather_api_key[-4:]}"
    print(f" Its unlocked. API key {masked_key}")



# # Exercise - Find the error
# new_crane = HeavyEquipment(machine_name="Liebherr-LTM", machine_type="Crane")
# db.add(new_crane)
# db.commit() # Don't forget to commit the new crane to the DB!

# missing_logs = db.query(HeavyEquipment.machine_name)\
#     .outerjoin(MaintenanceLog)\
#     .filter(MaintenanceLog.log_id.is_(None))\
#     .all()

# print("Machines with ZERO maintenance logs:")
# for machine in missing_logs:
#     print(f"- {machine[0]} has zero logs.")