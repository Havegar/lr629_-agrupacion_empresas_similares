#!/usr/bin/env python
# coding: utf-8

# ### Algoritmo de Louvain
# 
# En este notebook se plantea las relaciones societarias como base para el algoritmo de Louvain. Se seguira el siguiente approach:
# 
# - En primera instancia, no se considerara el valor de participacion societaria. Dependiendo de los resultados se proseguiracon la participacion y la ponderacion con patrimonio.
# - Es necesario agregar labels para saber efectivamente que nodos seran sociedades o personas naturales. El enfoque es agrupar sociedades.
# 
# - La data no sera manipulada de forma local.

# ### Se crea sesion en Spark


from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark import SparkContext, SparkConf
from pyspark.sql.types import StructType, StructField, DoubleType
from pyspark.sql.window import Window
from pyspark.sql.functions import col, row_number, count, lit

from pyspark.sql.functions import dense_rank

import networkx as nx
from cdlib import algorithms
from networkx.algorithms.community.quality import modularity
import os
import pyspark
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
import matplotlib.pyplot as plt

spark = SparkSession.builder \
  .appName("Test")  \
  .config("spark.kerberos.access.hadoopFileSystems","abfs://data@datalakesii.dfs.core.windows.net/") \
  .config("spark.executor.memory", "16g") \
  .config("spark.driver.memory", "12g")\
  .config("spark.executor.cores", "2") \
  .config("spark.executor.instances", "2") \
  .config("spark.driver.maxResultSize", "12g") \
  .getOrCreate()
warnings.filterwarnings('ignore', category=DeprecationWarning)
sc=spark.sparkContext
sc.setLogLevel ('ERROR')
spark.conf.set("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED")
spark.conf.set("spark.sql.parquet.enableVectorizedReader","false")
spark.conf.set("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED")
spark.conf.set("spark.sql.parquet.int96RebaseModeInWrite", "CORRECTED")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")


# ### Lectura de la malla de socios




spark.sql('select * from libsdf.jab_soc_2023_INOM').columns


# ### Ajuste de relaciones societarias



spark.sql('select RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES,PERI_AGNO_MES_TRIBUTARIO,FUENTE, count(*) as c from libsdf.jab_soc_2023_INOM group by RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES,PERI_AGNO_MES_TRIBUTARIO,FUENTE order by RUT_SOCIEDAD asc').createOrReplaceTempView("malla_societaria")
malla_noduplicados=spark.sql('select RUT_SOCIEDAD, RUT_SOCIO from malla_societaria ')
malla_noduplicados.createOrReplaceTempView("malla_societaria")
df_relaciones=malla_noduplicados.toPandas()


# In[6]:


df_relaciones


# ### Labels de nodos (persona natural o sociedad)

# In[7]:


spark.sql('SELECT RUT_SOCIEDAD AS RUT_UNICO FROM malla_societaria UNION SELECT RUT_SOCIO AS RUT_UNICO FROM malla_societaria').createOrReplaceTempView("entidades")
spark.sql('select count(*) from entidades').show()
spark.sql('SELECT DISTINCT(RUT_UNICO) FROM entidades').createOrReplaceTempView("entidades")
spark.sql('select count(*) from entidades').show()
spark.sql('SELECT * from libsdf.jab_materia_inom').createOrReplaceTempView("naturales")





df_entidades=spark.sql("select RUT_UNICO, CASE WHEN Valor IS NULL THEN 'SOCIEDAD' ELSE 'PERSONA' END AS TIPO  from entidades left join naturales on entidades.RUT_UNICO=naturales.CONT_RUT order by RUT_UNICO asc")
df_entidades=df_entidades.toPandas()
len(df_entidades)


# In[10]:


# Crear un grafo no dirigido, donde los nodos son RUT_SOCIEDAD y RUT_SOCIO
G = nx.Graph()
for _, row in df_relaciones.iterrows():
    G.add_node(row['RUT_SOCIEDAD'])
    G.add_node(row['RUT_SOCIO'])
    G.add_edge(row['RUT_SOCIEDAD'],row['RUT_SOCIO'])


# In[11]:


# Definir los valores del hiperparámetro de resolución que se quiere explorar
valores_resolucion = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
#valores_resolucion = [0.1]

df_entidades_final = df_entidades.copy()

# Crear listas para almacenar los valores de resolución y modularidad
resolucion_modularidad = []

# Iterar sobre los diferentes valores de resolución
for resolucion in valores_resolucion:
    # Aplicar el algoritmo de Louvain con el valor de resolución actual
    louvain_result = algorithms.louvain(G, resolution=resolucion)
    
    # Calcular la modularidad utilizando la función modularity de networkx
    modularity_value = modularity(G, louvain_result.communities)
    
    # Agregar el par (resolución, modularidad) a la lista
    resolucion_modularidad.append((resolucion, modularity_value))

    # Crear un DataFrame para mostrar nodos, comunidades y modularidad
    df_comunidades = pd.DataFrame(columns=['RUT_UNICO', f'comunidad_{resolucion}', f'modularidad_{resolucion}'])
    
    df_comunidades_list = []
    # Llenar el DataFrame con las comunidades detectadas
    for idx, comunidad in enumerate(louvain_result.communities):
        for node in comunidad:
            df_comunidades_list.append({'RUT_UNICO': node, f'comunidad_{resolucion}': idx+1, f'modularidad_{resolucion}': modularity_value})

    df_comunidades = pd.concat([df_comunidades, pd.DataFrame(df_comunidades_list)], ignore_index=True)  

    # Fusionar DataFrames utilizando la columna 'RUT_UNICO'
    df_entidades_final = pd.merge(df_entidades_final, df_comunidades, on='RUT_UNICO', how='left')

# Eliminar columnas redundantes
df_entidades_final = df_entidades_final.drop_duplicates()

# Guardar el DataFrame final como un archivo Parquet en la ubicación deseada
#df_to_parquet = spark.createDataFrame(df_entidades_final)
#df_to_parquet.write.mode('overwrite').format("parquet").save("abfs://data@datalakesii.dfs.core.windows.net/DatosOrigen/lr-629/agrupacion_empresas_similares/louvain_malla_societaria")


# In[12]:


df_entidades_final.to_csv('/home/cdsw/data/processed/louvain_malla_societaria/louvain_malla_societaria.csv', index=False)


# Desempaquetar los valores de resolución y modularidad de la lista resolucion_modularidad
resoluciones, modularidades = zip(*resolucion_modularidad)

# Guardar el DataFrame de resolución versus modularidad como un archivo CSV en la misma dirección que el otro archivo
df_resolucion_modularidad = pd.DataFrame({'resolucion': resoluciones, 'modularidad': modularidades})
df_resolucion_modularidad.to_csv('/home/cdsw/data/processed/louvain_malla_societaria/resolucion_modularidad.csv', index=False)




# Graficar modularidad versus resolución
plt.plot(resoluciones, modularidades, marker='o', linestyle='-')
plt.title('Modularidad vs Resolución')
plt.xlabel('Resolución')
plt.ylabel('Modularidad')
plt.grid(True)
plt.show()



