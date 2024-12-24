import networkx as nx
import pandas as pd
from sklearn.metrics import adjusted_mutual_info_score
from scipy.optimize import differential_evolution
import community as community_louvain
import numpy as np
import time

# Cargar los datos de relaciones y nodos
df_entidades = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/nodos.csv')

df_relaciones_contador = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_contador.csv')
df_relaciones_representante = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_representante.csv')
df_relaciones_familiares = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_familiares.csv')

# Leemos el subgrafo
G = nx.read_graphml("/home/cdsw/data/processed/subgrafo/muestreo_centralidad_gridsearch/subgraph_filtrado.graphml")

# Filtrar los nodos que tienen COM_INICIAL no nulo
df_entidades_filtrado = df_entidades.dropna(subset=['COM_INICIAL'])
nodos_filtrados = df_entidades_filtrado['RUT_UNICO'].tolist()

# Crear diccionario de índices para nodos
nodos_idx = {nodo: idx for idx, nodo in enumerate(G.nodes())}

# Convertir los DataFrames a numpy arrays para operaciones rápidas
relaciones_familiares = df_relaciones_familiares.values
relaciones_representante = df_relaciones_representante.values
relaciones_contador = df_relaciones_contador.values

# Filtrar las relaciones que están en el subgrafo para cada tipo de relación
relaciones_filtradas = {
    'familiares': relaciones_familiares[np.array([G.has_edge(row[0], row[1]) for row in relaciones_familiares])],
    'representantes': relaciones_representante[np.array([G.has_edge(row[0], row[1]) for row in relaciones_representante])],
    'contadores': relaciones_contador[np.array([G.has_edge(row[0], row[1]) for row in relaciones_contador])]
}

del df_relaciones_contador
del df_relaciones_representante
del df_relaciones_familiares

# Contador de iteraciones
iteration_counter = 0

# DataFrame para almacenar resultados
df_resultados = pd.DataFrame(columns=['Iteración', 'Valor_familiares', 'Valor_representantes', 'Valor_contadores', 'Resolución', 'Valor_AMI'])


def calcular_AMI(parametros):
    global iteration_counter
    iteration_counter += 1
    valor_familiares, valor_representantes, valor_contadores, resolucion = parametros
    
    # Crear una copia del grafo original
    G_temp = G.copy()
    
    # Medir el tiempo de actualización de valores de relaciones
    start_update_time = time.time()

    # Crear listas de aristas con nuevos pesos
    edges_familiares = [(row[0], row[1], valor_familiares) for row in relaciones_filtradas['familiares']]
    edges_representantes = [(row[0], row[1], valor_representantes) for row in relaciones_filtradas['representantes']]
    edges_contadores = [(row[0], row[1], valor_contadores) for row in relaciones_filtradas['contadores']]

    # Actualizar los pesos en el grafo temporal usando add_weighted_edges_from
    G_temp.add_weighted_edges_from(edges_familiares)
    G_temp.add_weighted_edges_from(edges_representantes)
    G_temp.add_weighted_edges_from(edges_contadores)

    update_time = time.time() - start_update_time

    # Aplicar el algoritmo de Louvain
    louvain_start_time = time.time()
    louvain_result = community_louvain.best_partition(G_temp, partition=None, weight='weight', resolution=resolucion, randomize=None, random_state=100)
    louvain_time = time.time() - louvain_start_time
    
    # Filtrar nodos con COM_INICIAL no nulo para calcular AMI
    nodos_con_comunidad_inicial = [nodo for nodo in nodos_filtrados if pd.notnull(df_entidades_filtrado.loc[df_entidades_filtrado['RUT_UNICO'] == nodo, 'COM_INICIAL'].iloc[0])]
    
    # Calcular AMI entre 'COM_INICIAL' y la comunidad encontrada para los nodos filtrados
    df_comunidades_list = [{'RUT_UNICO': nodo, 'COM_INICIAL': df_entidades_filtrado.loc[df_entidades_filtrado['RUT_UNICO'] == nodo, 'COM_INICIAL'].iloc[0], 'comunidad': louvain_result.get(nodo, None)} for nodo in nodos_con_comunidad_inicial]
    df_comunidades = pd.DataFrame(df_comunidades_list)
    df_filtered = df_comunidades.dropna(subset=['comunidad', 'COM_INICIAL'])
    
    ami_score = adjusted_mutual_info_score(df_filtered['COM_INICIAL'], df_filtered['comunidad'])

    # Imprimir los valores de cada combinación y los tiempos de ejecución
    print(f"Iteración {iteration_counter}")
    print(f"Parámetros: Familiares={valor_familiares}, Representantes={valor_representantes}, Contadores={valor_contadores}, Resolución={resolucion}")
    print(f"AMI: {-ami_score}, Tiempo de actualización relaciones: {update_time}, Tiempo de Louvain: {louvain_time}")
    print("-" * 50)
    # Guardar resultados en el DataFrame
    global df_resultados
    df_resultados.loc[len(df_resultados)] = [iteration_counter, valor_familiares, valor_representantes, valor_contadores, resolucion, -ami_score]

    df_resultados.to_csv('/home/cdsw/data/processed/resultados_subgrafo_gridsearch/gridsearch_optimizator.csv', index=False)
    return -ami_score

# Definir los límites del espacio de búsqueda
bounds = [(0.1, 1), (0.1, 1), (0.1, 1), (0.1, 0.4)]  # límites para los valores de relación y resolución

# Ejecutar Differential Evolution con parámetros ajustados
resultado = differential_evolution(
    calcular_AMI, 
    bounds,
    maxiter=500,  # Número máximo de generaciones
    tol=1e-3,  # Tolerancia para el cambio en el valor objetivo, ajustada a una milésima
    popsize=15,  # Tamaño de la población
    mutation=(0.5, 1),  # Factor de mutación
    recombination=0.7,  # Tasa de recombinación
    disp=True,  # Mostrar información sobre el progreso
    polish=True  # Optimización local usando BFGS al final
)

# Mejor valor de AMI encontrado
mejor_ami = -resultado.fun
mejores_parametros = resultado.x

print("Mejor AMI:", mejor_ami)
print("Mejores parámetros:")
print("  Valor de familiares:", mejores_parametros[0])
print("  Valor de representantes:", mejores_parametros[1])
print("  Valor de contadores:", mejores_parametros[2])
print("  Resolución:", mejores_parametros[3])