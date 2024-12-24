import networkx as nx
from cdlib import algorithms
from networkx.algorithms.community.quality import modularity
import pandas as pd
import json
import warnings
import community as community_louvain
from sklearn.metrics import adjusted_mutual_info_score

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Cargar los datos de las relaciones
df_relaciones_malla = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_malla_societaria.csv')
df_relaciones_contador = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_contador.csv')
df_relaciones_representante = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_representante.csv')
df_relaciones_familiares = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_familiares.csv')
df_entidades = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/nodos.csv')

# Cargar los grupos iniciales de contribuyentes
ruta_archivo = '/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/grupos_previos.json'
with open(ruta_archivo, 'r') as archivo:
    grupos_previos = json.load(archivo)

# Cargar el CSV con los resultados de la optimización
df_gridsearch = pd.read_csv('/home/cdsw/data/processed/resultados_subgrafo_gridsearch/gridsearch_optimizator.csv')

# Encontrar la fila con el menor valor de AMI
fila_min_ami = df_gridsearch.loc[df_gridsearch['Valor_AMI'].idxmin()]

# Extraer los pesos y resolución
peso_familiares = round(fila_min_ami['Valor_familiares'], 6)
peso_representantes = round(fila_min_ami['Valor_representantes'], 6)
peso_contadores = round(fila_min_ami['Valor_contadores'], 6)
resolucion = round(fila_min_ami['Resolución'], 6)


print(f"Peso Familiares: {peso_familiares}")
print(f"Peso Representantes: {peso_representantes}")
print(f"Peso Contadores: {peso_contadores}")
print(f"Resolución: {resolucion}")

# Construcción del grafo completo
G = nx.Graph()

# Añadir relaciones societarias
for _, row in df_relaciones_malla.iterrows():
    G.add_edge(row['RUT_SOCIEDAD'], row['RUT_SOCIO'], weight=row['peso'])

# Aplicar pesos de las relaciones según la optimización
for _, row in df_relaciones_familiares.iterrows():
    G.add_edge(row['CONT_RUT'], row['RUT_FAM'], weight=peso_familiares)

for _, row in df_relaciones_representante.iterrows():
    G.add_edge(row['CONT_RUT'], row['CONT_RUT_REPRESENTANTE'], weight=peso_representantes)

for _, row in df_relaciones_contador.iterrows():
    G.add_edge(row['CONT_RUT'], row['RUT_CONTADOR'], weight=peso_contadores)

# Algoritmo de Louvain
louvain_result = community_louvain.best_partition(G, weight='weight', resolution=resolucion)
comunidades = {}
for nodo, comunidad in louvain_result.items():
    if comunidad not in comunidades:
        comunidades[comunidad] = set()
    comunidades[comunidad].add(nodo)
comunidades = list(comunidades.values())

# Calcular la modularidad
modularity_value = modularity(G, comunidades)

# Guardar los resultados
df_comunidades_list = [{'RUT_UNICO': nodo, f'comunidad_{resolucion}': comunidad + 1} for nodo, comunidad in louvain_result.items()]
df_comunidades = pd.DataFrame(df_comunidades_list)
df_entidades = pd.merge(df_entidades, df_comunidades, on='RUT_UNICO', how='left')
df_entidades.to_csv('/home/cdsw/data/processed/resultados_finales/louvain/louvain_all.csv', index=False)

df_entidades=df_entidades.dropna()

#Iniciar sesion de spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark import SparkContext, SparkConf
import pyspark

spark = SparkSession.builder \
  .appName("Test")  \
  .config("spark.yarn.access.hadoopFileSystems","abfs://data@datalakesii.dfs.core.windows.net/") \
  .config("spark.executor.memory", "24g") \
  .config("spark.driver.memory", "12g")\
  .config("spark.executor.cores", "12") \
  .config("spark.executor.instances", "24") \
  .config("spark.driver.maxResultSize", "12g") \
  .getOrCreate()

warnings.filterwarnings('ignore', category=DeprecationWarning)
sc=spark.sparkContext
sc.setLogLevel ('ERROR')


df_entidades_spark = spark.createDataFrame(df_entidades)
# Guarda el DataFrame de Spark en formato Parquet
df_entidades_spark.write.parquet("abfs://data@datalakesii.dfs.core.windows.net/DatosOrigen/lr-629/agrupacion_empresas_similares/louvain_final")

# Detiene la sesión de Spark 
spark.stop()

# Cálculo del AMI
ami_score = adjusted_mutual_info_score(
    df_entidades['COM_INICIAL'], 
    df_entidades[f'comunidad_{resolucion}']
)

# Guardar el resultado en un DataFrame
df_ami = pd.DataFrame({'Resolucion': [resolucion], 'AMI': [ami_score]})
df_ami.to_csv('/home/cdsw/data/processed/resultados_finales/louvain/resolucion_ami.csv', index=False)

# Imprimir resultados

print(f"Modularidad: {modularity_value}")
print(f"AMI: {ami_score}")

