from ortools.sat.python import cp_model
class Persona:
    def __init__(self, nombre, amistades=None, enemistades=None):
        self.nombre = nombre
        self.amistades = amistades or []
        self.enemistades = enemistades or []

personas = [
    Persona("Ana", amistades=["Luis"]),
    Persona("Luis", amistades=["Ana", "Sofía"]),
    Persona("Marta", enemistades=["Pedro"]),
    Persona("Pedro", enemistades=["Marta"]),
    Persona("Sofía", amistades=["Luis"], enemistades=["Marta"]),
]

def asignar_mesas(participantes, tamano_mesa):
    model = cp_model.CpModel()

    nombres = [p.nombre for p in participantes]
    num_mesas = len(participantes) // tamano_mesa + 1

    # Variables: mesa asignada a cada persona
    mesas = {
        nombre: model.NewIntVar(0, num_mesas - 1, nombre)
        for nombre in nombres
    }

    # Restricciones de amistad y enemistad
    for p in participantes:
        for amigo in p.amistades:
            if amigo in mesas:
                model.Add(mesas[p.nombre] == mesas[amigo])
        for enemigo in p.enemistades:
            if enemigo in mesas:
                model.Add(mesas[p.nombre] != mesas[enemigo])

    # Restricción de tamaño máximo por mesa
    # Usamos variables booleanas para controlar cuántas personas hay en cada mesa
    for m in range(num_mesas):
        # Para cada mesa, creamos indicadores de quién está allí
        indicators = []
        for nombre in nombres:
            b = model.NewBoolVar(f"{nombre}_en_mesa_{m}")
            # Si mesa[nombre] == m, entonces b = 1
            model.Add(mesas[nombre] == m).OnlyEnforceIf(b)
            model.Add(mesas[nombre] != m).OnlyEnforceIf(b.Not())
            indicators.append(b)
        # Máximo tamano_mesa personas por mesa
        model.Add(sum(indicators) <= tamano_mesa)

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    # Resultado
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {nombre: solver.Value(mesas[nombre]) for nombre in nombres}
    else:
        return None
    
sol = asignar_mesas(personas, tamano_mesa=3)
print(sol)