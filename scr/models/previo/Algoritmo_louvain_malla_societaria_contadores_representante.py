#!/usr/bin/env python
# coding: utf-8

# ### Algoritmo de Louvain
# 
# En este notebook se plantea las relaciones societarias y los contadores como base para el algoritmo de Louvain. Se seguira el siguiente approach:
# 
# - En primera instancia, no se considerara el valor de participacion societaria ni fuerzas con caracter numerico.
# - Es necesario agregar labels para saber efectivamente que nodos seran sociedades, personas naturales o contadores. El enfoque es agrupar sociedades.
# 

# ### Se crea sesion en Spark

# In[1]:


#spark.stop


# In[2]:


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


# In[3]:


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

# In[4]:


spark.sql('select * from libsdf.jab_soc_2023_INOM').columns


# ### Ajuste de relaciones societarias (quitar duplicados)

# In[5]:


spark.sql('select RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES,PERI_AGNO_MES_TRIBUTARIO,FUENTE, count(*) as c from libsdf.jab_soc_2023_INOM group by RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES,PERI_AGNO_MES_TRIBUTARIO,FUENTE order by RUT_SOCIEDAD asc').createOrReplaceTempView("malla_societaria")
malla_noduplicados=spark.sql('select RUT_SOCIEDAD, RUT_SOCIO from malla_societaria order by RUT_SOCIEDAD ASC')
malla_noduplicados.createOrReplaceTempView("malla_societaria")
df_relaciones_malla=malla_noduplicados.toPandas()


# In[6]:


df_relaciones_malla


# ### Labels de nodos (persona natural o sociedad) a partir de tabla de oscuridad de persona natural

# In[7]:


spark.sql('SELECT RUT_SOCIEDAD AS RUT_UNICO FROM malla_societaria UNION SELECT RUT_SOCIO AS RUT_UNICO FROM malla_societaria').createOrReplaceTempView("entidades")
spark.sql('select count(*) from entidades').show()
spark.sql('SELECT DISTINCT(RUT_UNICO) FROM entidades').createOrReplaceTempView("entidades")
spark.sql('select count(*) from entidades').show()
spark.sql('SELECT * from libsdf.jab_materia_inom').createOrReplaceTempView("naturales")


# In[8]:


# Se verifica en este caso que la tabla de materia oscura no tiene valores nulos
spark.sql('select count(*) from naturales where Valor is null').show()


# In[9]:


### guardamos los datos de todas las entidaddes de la malla societaria, indicando si se trata de una sociedad o persona natural
df_entidades=spark.sql("select RUT_UNICO, CASE WHEN Valor IS NULL THEN 'SOCIEDAD' ELSE 'PERSONA' END AS TIPO  from entidades left join naturales on entidades.RUT_UNICO=naturales.CONT_RUT order by RUT_UNICO asc")
df_entidades.createOrReplaceTempView("entidades")


# In[10]:


spark.sql('select COUNT(*) from entidades').show()


# ### Lectura de datos de contadores y definicion de tipos de RUT, construccion de relaciones

# In[11]:


spark.sql('SELECT * from libsdf.arfi_contadores_e order by CONT_RUT asc').createOrReplaceTempView("data_contador")
spark.sql('SELECT CONT_RUT from data_contador').createOrReplaceTempView("tiene_contador")
spark.sql('select tiene_contador.CONT_RUT as RUT_UNICO, CASE WHEN Valor IS NULL THEN "SOCIEDAD" ELSE "PERSONA"  END AS TIPO from tiene_contador left join naturales on tiene_contador.CONT_RUT=naturales.CONT_RUT').createOrReplaceTempView("tiene_contador")
spark.sql('SELECT DISTINCT RUT_CONTADOR as RUT_UNICO, "CONTADOR" AS TIPO FROM data_contador').createOrReplaceTempView("contadores")


# In[12]:


# Construccion de relaciones de contadores
df_relaciones_contador=spark.sql('select CONT_RUT,RUT_CONTADOR from libsdf.arfi_contadores_e WHERE CONT_RUT IS NOT NULL AND RUT_CONTADOR IS NOT NULL').toPandas()


# ### Unificacion de data de contadores con data de malla societaria

# In[13]:


spark.sql('SELECT RUT_UNICO, TIPO FROM entidades UNION SELECT RUT_UNICO, TIPO FROM tiene_contador UNION SELECT RUT_UNICO, TIPO FROM contadores').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO, count(*) as c from entidades group by RUT_UNICO,TIPO').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO from entidades').createOrReplaceTempView("entidades")
# dejamos el label mas actual de cada nodo, en este caso se sobreescribe con el label 'contador'
spark.sql('SELECT RUT_UNICO, CASE  WHEN COUNT(*) > 1 AND SUM(CASE WHEN TIPO = "CONTADOR" THEN 1 ELSE 0 END) > 0 THEN "CONTADOR" ELSE MAX(TIPO) END AS TIPO FROM  entidades GROUP BY RUT_UNICO').createOrReplaceTempView("entidades")


# In[14]:


spark.sql('select COUNT(*) from entidades').show()


# ### Lectura de datos de representantes y definicion de tipos de RUT, construccion de relaciones

# In[15]:


spark.sql('SELECT repr_fecha_inicio_vo,cont_rut,cont_rut_representante,repr_fecha_termino_vo from dw.dw_trn_djr_representantes_e').createOrReplaceTempView("data_rep")
#filtramos los datos para seleccionar el representante o representantes vigentes el 2023
spark.sql('SELECT repr_fecha_inicio_vo,cont_rut,cont_rut_representante,repr_fecha_termino_vo  FROM  data_rep  WHERE  repr_fecha_inicio_vo < "2024-01-01" AND (repr_fecha_termino_vo IS NULL OR repr_fecha_termino_vo > "2023-01-01") order by repr_fecha_inicio_vo desc').createOrReplaceTempView("data_rep")
spark.sql('SELECT cont_rut as CONT_RUT,cont_rut_representante as CONT_RUT_REPRESENTANTE FROM  data_rep').createOrReplaceTempView("data_rep")


# In[16]:


#Construccion de relaciones de representantes
df_relaciones_representante=spark.sql('select * from data_rep WHERE CONT_RUT IS NOT NULL AND CONT_RUT_REPRESENTANTE IS NOT NULL').toPandas()


# In[17]:


spark.sql('SELECT CONT_RUT from data_rep').createOrReplaceTempView("tiene_rep")
spark.sql('select tiene_rep.CONT_RUT as RUT_UNICO, CASE WHEN Valor IS NULL THEN "SOCIEDAD" ELSE "PERSONA"  END AS TIPO from tiene_rep left join naturales on tiene_rep.CONT_RUT=naturales.CONT_RUT').createOrReplaceTempView("tiene_rep")
spark.sql('SELECT DISTINCT cont_rut_representante as RUT_UNICO, "REPRESENTANTE" AS TIPO FROM data_rep').createOrReplaceTempView("representantes")


# ### Unificacion de data de representantes con data de malla societaria

# In[18]:


spark.sql('SELECT RUT_UNICO, TIPO FROM entidades UNION SELECT RUT_UNICO, TIPO FROM tiene_rep UNION SELECT RUT_UNICO, TIPO FROM representantes').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO, count(*) as c from entidades group by RUT_UNICO,TIPO').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO from entidades').createOrReplaceTempView("entidades")
# dejamos el label mas actual de cada nodo, en este caso se sobreescribe con el label 'representante'
spark.sql('SELECT RUT_UNICO, CASE  WHEN COUNT(*) > 1 AND SUM(CASE WHEN TIPO = "REPRESENTANTE" THEN 1 ELSE 0 END) > 0 THEN "REPRESENTANTE" ELSE MAX(TIPO) END AS TIPO FROM  entidades GROUP BY RUT_UNICO').createOrReplaceTempView("entidades")


# In[19]:


#Se llevan todas las entidades involucradas a dataframe de pandas
df_entidades=spark.sql('select * from entidades')
df_entidades=df_entidades.toPandas()
len(df_entidades)


# In[20]:


G = nx.Graph()
# cargamos relaciones, con nodos RUT_SOCIEDAD y RUT_SOCIO
for _, row in df_relaciones_malla.iterrows():
    G.add_node(row['RUT_SOCIEDAD'])
    G.add_node(row['RUT_SOCIO'])
    G.add_edge(row['RUT_SOCIEDAD'],row['RUT_SOCIO'])
    
# cargamos relaciones, con nodos CONT_RUT y RUT_CONTADOR
for _, row in df_relaciones_contador.iterrows():
    G.add_node(row['CONT_RUT'])
    G.add_node(row['RUT_CONTADOR'])
    G.add_edge(row['CONT_RUT'],row['RUT_CONTADOR'])
    
# cargamos relaciones, con nodos cont_rut y cont_rut_representante
for _, row in df_relaciones_representante.iterrows():
    G.add_node(row['CONT_RUT'])
    G.add_node(row['CONT_RUT_REPRESENTANTE'])
    G.add_edge(row['CONT_RUT'],row['CONT_RUT_REPRESENTANTE'])   
    



# In[21]:


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



df_entidades_final.to_csv('/home/cdsw/data/processed/louvain_malla_societaria_contador_representante/louvain_malla_societaria_contador_representante.csv', index=False)

# Desempaquetar los valores de resolución y modularidad de la lista resolucion_modularidad
resoluciones, modularidades = zip(*resolucion_modularidad)

# Guardar el DataFrame de resolución versus modularidad como un archivo CSV en la misma dirección que el otro archivo
df_resolucion_modularidad = pd.DataFrame({'resolucion': resoluciones, 'modularidad': modularidades})


# In[23]:


# Desempaquetar los valores de resolución y modularidad de la lista resolucion_modularidad
resoluciones, modularidades = zip(*resolucion_modularidad)

# Guardar el DataFrame de resolución versus modularidad como un archivo CSV en la misma dirección que el otro archivo
df_resolucion_modularidad = pd.DataFrame({'resolucion': resoluciones, 'modularidad': modularidades})
df_resolucion_modularidad.to_csv('/home/cdsw/data/processed/louvain_malla_societaria_contador_representante/resolucion_modularidad.csv', index=False)

# Graficar modularidad versus resolución
plt.plot(resoluciones, modularidades, marker='o', linestyle='-')
plt.title('Modularidad vs Resolución')
plt.xlabel('Resolución')
plt.ylabel('Modularidad')
plt.grid(True)
plt.show()

