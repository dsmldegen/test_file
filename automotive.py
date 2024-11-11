import time
from gurobipy import GRB, Model

# Example data
# Component capacities at parts plants
parts_capacity = {
    ('parts_plant1', 'chassis'): 50000,
    ('parts_plant1', 'engine'): 40000,
    ('parts_plant1', 'electronics'): 54000,  # 10% reduction from 60000
    ('parts_plant2', 'chassis'): 30000,
    ('parts_plant2', 'engine'): 35000,
    ('parts_plant2', 'electronics'): 45000,
    ('parts_plant3', 'chassis'): 40000,
    ('parts_plant3', 'engine'): 30000,
    ('parts_plant3', 'electronics'): 50000
}

# Transport costs for components
transport_cost_parts_to_assembly = {
    ('parts_plant1', 'assembly_plant1', 'chassis'): 400,
    ('parts_plant1', 'assembly_plant1', 'engine'): 300,
    ('parts_plant1', 'assembly_plant1', 'electronics'): 200,
    ('parts_plant1', 'assembly_plant2', 'chassis'): 350,
    ('parts_plant1', 'assembly_plant2', 'engine'): 250,
    ('parts_plant1', 'assembly_plant2', 'electronics'): 180,
    ('parts_plant2', 'assembly_plant1', 'chassis'): 380,
    ('parts_plant2', 'assembly_plant1', 'engine'): 280,
    ('parts_plant2', 'assembly_plant1', 'electronics'): 190,
    ('parts_plant2', 'assembly_plant2', 'chassis'): 340,
    ('parts_plant2', 'assembly_plant2', 'engine'): 240,
    ('parts_plant2', 'assembly_plant2', 'electronics'): 170,
    ('parts_plant3', 'assembly_plant1', 'chassis'): 360,
    ('parts_plant3', 'assembly_plant1', 'engine'): 260,
    ('parts_plant3', 'assembly_plant1', 'electronics'): 180,
    ('parts_plant3', 'assembly_plant2', 'chassis'): 320,
    ('parts_plant3', 'assembly_plant2', 'engine'): 220,
    ('parts_plant3', 'assembly_plant2', 'electronics'): 160
}

# Assembly costs per vehicle model
assembly_cost_basic = {
    'assembly_plant1': 12000,
    'assembly_plant2': 13000
}

assembly_cost_luxury = {
    'assembly_plant1': 18000,
    'assembly_plant2': 20000
}

# Shipping costs to dealerships
shipping_cost_to_dealership = {
    ('assembly_plant1', 'dealer_region1', 'basic'): 700,
    ('assembly_plant1', 'dealer_region2', 'basic'): 600,
    ('assembly_plant1', 'dealer_region3', 'basic'): 900,
    ('assembly_plant1', 'dealer_region1', 'luxury'): 800,
    ('assembly_plant1', 'dealer_region2', 'luxury'): 700,
    ('assembly_plant1', 'dealer_region3', 'luxury'): 1000,
    ('assembly_plant2', 'dealer_region1', 'basic'): 650,
    ('assembly_plant2', 'dealer_region2', 'basic'): 750,
    ('assembly_plant2', 'dealer_region3', 'basic'): 500,
    ('assembly_plant2', 'dealer_region1', 'luxury'): 750,
    ('assembly_plant2', 'dealer_region2', 'luxury'): 850,
    ('assembly_plant2', 'dealer_region3', 'luxury'): 600
}

# Quarterly demand by dealer region
basic_demand = {
    'dealer_region1': 1000,  # Reduced from 5000
    'dealer_region2': 1600,  # Reduced from 8000
    'dealer_region3': 1200   # Reduced from 6000
}

luxury_demand = {
    'dealer_region1': 600,   # Reduced from 3000
    'dealer_region2': 400,   # Reduced from 2000
    'dealer_region3': 800    # Reduced from 4000
}

# Component requirements per vehicle type
component_requirements = {
    ('basic', 'chassis'): 1,
    ('basic', 'engine'): 1,
    ('basic', 'electronics'): 1,
    ('luxury', 'chassis'): 1,
    ('luxury', 'engine'): 1,
    ('luxury', 'electronics'): 2  # Luxury models need more electronics
}

# Paint shop capacity (vehicles per quarter)
paint_shop_capacity = {
    'assembly_plant1': 25000,
    'assembly_plant2': 30000
}

# Labor hours available per quarter
labor_hours = {
    'assembly_plant1': 70000,  # Increased from 10000
    'assembly_plant2': 88000   # Increased from 12000
}

# Labor hours required per vehicle type
labor_requirements = {
    'basic': 15,    # Reduced from 20 hours
    'luxury': 25    # Reduced from 30 hours
}


# OPTIGUIDE DATA CODE GOES HERE

# Derive sets for indexing
dealer_regions = list(set(i[1] for i in shipping_cost_to_dealership.keys()))
assembly_plants = list(set(i[0] for i in shipping_cost_to_dealership.keys()))
parts_plants = list(set(i[0] for i in transport_cost_parts_to_assembly.keys()))
component_types = list(set(i[2] for i in transport_cost_parts_to_assembly.keys()))

# Create optimization model
model = Model("auto_manufacturing")

# Create variables
# Component shipments
x = model.addVars(transport_cost_parts_to_assembly.keys(),
                  vtype=GRB.INTEGER,
                  name="x")

# Vehicle shipments
y_basic = model.addVars(shipping_cost_to_dealership.keys(),
                       vtype=GRB.INTEGER,
                       name="y_basic")
y_luxury = model.addVars(shipping_cost_to_dealership.keys(),
                        vtype=GRB.INTEGER,
                        name="y_luxury")

# Set objective
model.setObjective(
    # Component transport costs
    sum(x[i] * transport_cost_parts_to_assembly[i]
        for i in transport_cost_parts_to_assembly.keys()) +
    # Assembly and shipping costs
    sum(assembly_cost_basic[p] * y_basic[p, d, 'basic'] +
        assembly_cost_luxury[p] * y_luxury[p, d, 'luxury']
        for p in assembly_plants
        for d in dealer_regions) +
    # Delivery costs
    sum(y_basic[j] * shipping_cost_to_dealership[j] +
        y_luxury[j] * shipping_cost_to_dealership[j]
        for j in shipping_cost_to_dealership.keys()),
    GRB.MINIMIZE)

# Component flow constraints at assembly plants
for p in assembly_plants:
    for c in component_types:
        model.addConstr(
            sum(x[s, p, c] for s in parts_plants) ==
            sum(y_basic[p, d, 'basic'] * component_requirements['basic', c] +
                y_luxury[p, d, 'luxury'] * component_requirements['luxury', c]
                for d in dealer_regions),
            f"flow_{p}_{c}")

# Parts plant capacity constraints
for s in parts_plants:
    for c in component_types:
        model.addConstr(
            sum(x[s, p, c] for p in assembly_plants) <= parts_capacity[s, c],
            f"capacity_{s}_{c}")

# Dealer region demand constraints
for d in dealer_regions:
    model.addConstr(
        sum(y_basic[p, d, 'basic'] for p in assembly_plants) >= basic_demand[d],
        f"basic_demand_{d}")
    model.addConstr(
        sum(y_luxury[p, d, 'luxury'] for p in assembly_plants) >= luxury_demand[d],
        f"luxury_demand_{d}")

# Paint shop capacity constraints
for p in assembly_plants:
    model.addConstr(
        sum(y_basic[p, d, 'basic'] + y_luxury[p, d, 'luxury']
            for d in dealer_regions) <= paint_shop_capacity[p],
        f"paint_{p}")

# Labor hour constraints
for p in assembly_plants:
    model.addConstr(
        sum(y_basic[p, d, 'basic'] * labor_requirements['basic'] +
            y_luxury[p, d, 'luxury'] * labor_requirements['luxury']
            for d in dealer_regions) <= labor_hours[p],
        f"labor_{p}")

# Optimize model
model.optimize()
m = model

# OPTIGUIDE CONSTRAINT CODE GOES HERE

# Solve
m.update()
model.optimize()

print(time.ctime())
if m.status == GRB.OPTIMAL:
    print(f'Optimal total cost: ${m.objVal:,.2f}')
    
    # Print detailed production plan
    print("\nProduction Plan by Plant:")
    for p in assembly_plants:
        print(f"\n{p}:")
        basic_total = sum(y_basic[p,d,'basic'].X for d in dealer_regions)
        luxury_total = sum(y_luxury[p,d,'luxury'].X for d in dealer_regions)
        print(f"Basic models: {basic_total:,.0f}")
        print(f"Luxury models: {luxury_total:,.0f}")
        
        # Calculate utilization metrics
        total_vehicles = basic_total + luxury_total
        print(f"Paint shop utilization: {(total_vehicles/paint_shop_capacity[p])*100:.1f}%")
        
        labor_used = (basic_total * labor_requirements['basic'] +
                     luxury_total * labor_requirements['luxury'])
        print(f"Labor utilization: {(labor_used/labor_hours[p])*100:.1f}%")

    # Print component usage
    print("\nComponent Usage by Parts Plant:")
    for s in parts_plants:
        print(f"\n{s}:")
        for c in component_types:
            usage = sum(x[s,p,c].X for p in assembly_plants)
            capacity = parts_capacity[s,c]
            print(f"{c}: {usage:,.0f}/{capacity:,.0f} ({(usage/capacity)*100:.1f}% utilization)")
else:
    print("Not solved to optimality. Status:", m.status)