#!/usr/bin/env python
# coding: utf-8

# ## Calculo de relaciones de diverso tipo, nodos, etiquetas, contibuyentes involucrados y cruce con grupos economicos previo a algoritmos de particion.

# En este notebook se realizara la coleccion de diversas capas de relaciones. Se considera:
# - Uso de relaciones societarias, de representante y de contador.
# - Un peso para cada una de estas relaciones. En particular, para la malla societaria, se utilizara un valor de 0 a 1 correspondiente al valor de participacion.
# - Estas relaciones y nodos se guardaran en dos archivos correspondientes para su utilizacion posterior en el algoritmo de Louvain. 
# - Se obtiene tambien un archivo con cada contribuyente y su tipo, dependiendo de la tabla de origen.
# - Se considera la reaccion de un diccionario que permite un estado inicial, considerando los grupos economicos establecidos por criterio experto. 

# In[1]:


from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark import SparkContext, SparkConf
from pyspark.sql.types import StructType, StructField, DoubleType
from pyspark.sql.window import Window
from pyspark.sql.functions import col, row_number, count, lit
import community as community_louvain
from pyspark.sql.functions import dense_rank


# In[2]:


import networkx as nx
from cdlib import algorithms
from networkx.algorithms.community.quality import modularity
import os
import json
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
  .config("spark.driver.maxResultSize", "0") \
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


# ## Lectura de la malla de socios

# In[4]:


spark.sql('select RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES,PERI_AGNO_MES_TRIBUTARIO,FUENTE, count(*) as c from libsdf.jab_soc_2023_INOM group by RUT_SOCIEDAD,RUT_SOCIO,PORCENTAJE_CAPITAL,PORCENTAJE_UTILIDADES,PERI_AGNO_MES_TRIBUTARIO,FUENTE order by RUT_SOCIEDAD asc').createOrReplaceTempView("malla_societaria")
malla_noduplicados=spark.sql('select RUT_SOCIEDAD, RUT_SOCIO, PORCENTAJE_CAPITAL/100 as peso from malla_societaria  where RUT_SOCIEDAD is not null AND RUT_SOCIO is not null AND PORCENTAJE_CAPITAL is not null order by RUT_SOCIEDAD asc')
malla_noduplicados.createOrReplaceTempView("malla_societaria")
df_relaciones_malla=malla_noduplicados.toPandas()

df_relaciones_malla.to_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_malla_societaria.csv', index=False)


# ## Labels de nodos (persona natural o sociedad) a partir de tabla de oscuridad de persona natural

# In[5]:


spark.sql('SELECT DISTINCT(RUT_SOCIEDAD) AS RUT_UNICO FROM malla_societaria UNION SELECT DISTINCT(RUT_SOCIO) AS RUT_UNICO FROM malla_societaria').createOrReplaceTempView("aux")
spark.sql('SELECT DISTINCT(RUT_UNICO) as RUT_UNICO FROM aux').createOrReplaceTempView("entidades")
spark.sql('select count(*) from entidades').show()
spark.sql('select count(distinct(*)) from entidades').show()


# In[6]:


spark.sql('SELECT CONT_RUT, AVG(Valor) as Valor from libsdf.jab_materia_inom group by CONT_RUT').createOrReplaceTempView("naturales")


# In[7]:


### guardamos los datos de todas las entidaddes de la malla societaria, indicando si se trata de una sociedad o persona natural
spark.sql("select RUT_UNICO, CASE WHEN Valor IS NULL THEN 'SOCIEDAD' ELSE 'PERSONA' END AS TIPO  from entidades left join naturales on entidades.RUT_UNICO=naturales.CONT_RUT order by RUT_UNICO asc").createOrReplaceTempView("entidades")


# In[8]:


spark.sql('select COUNT(*) from entidades').show()


# In[9]:


spark.sql('select COUNT(DISTINCT(RUT_UNICO)) from entidades').show()


# ## Lectura de datos de familiares

# In[10]:


#Se lee la data,se descartan las entradas erroneas.
# Selecionaremos solo las relaciones de  HIJO, CONYUGE
spark.read.parquet("abfs://data@datalakesii.dfs.core.windows.net/DatosOrigen/LibSDF/REL_FAMILIARES_AARI_EH").createOrReplaceTempView("familiares")
spark.sql('select * from familiares where CONT_RUT is not null AND RUT_FAM IS NOT NULL AND TIPO_RELACION IS NOT NULL order by CONT_RUT asc').createOrReplaceTempView("familiares")
spark.sql('select CONT_RUT, RUT_FAM, TIPO_RELACION from familiares where TIPO_RELACION <> "TIPO_RELACION" and CONT_RUT<> RUT_FAM').createOrReplaceTempView("familiares")
spark.sql('select CONT_RUT, RUT_FAM, TIPO_RELACION from familiares where (TIPO_RELACION ="HIJO" OR TIPO_RELACION ="CONYUGE")').createOrReplaceTempView("familiares")
spark.sql('select TIPO_RELACION, count(*) as c from familiares group by TIPO_RELACION').show()
spark.sql('select CONT_RUT, RUT_FAM, count(*) as c from familiares group by CONT_RUT, RUT_FAM').createOrReplaceTempView("familiares")
spark.sql('select  CONT_RUT, RUT_FAM from familiares').createOrReplaceTempView("familiares")


# ## Construccion de relaciones  familiares

# In[ ]:


df_relaciones_familiares=spark.sql('select CONT_RUT,RUT_FAM, 1 as peso from familiares').toPandas()
df_relaciones_familiares.to_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_familiares.csv', index=False)


# ## Agregacion de labels al pool de entidades

# In[ ]:


# Se agregan los datos de las personas naturales familiares al pool de entidades
spark.sql('SELECT DISTINCT(CONT_RUT) as RUT_UNICO, "PERSONA" AS TIPO FROM familiares UNION SELECT DISTINCT(RUT_FAM) as RUT_UNICO, "PERSONA" AS TIPO FROM familiares UNION SELECT RUT_UNICO, TIPO FROM entidades').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO, count(*) as c from entidades group by RUT_UNICO,TIPO').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO from entidades').createOrReplaceTempView("entidades")

spark.sql('select COUNT(*) from entidades').show()


# ## Lectura de datos de contadores y definicion de tipos de RUT

# In[ ]:


spark.sql('SELECT * from libsdf.arfi_contadores_e WHERE CONT_RUT IS NOT NULL AND RUT_CONTADOR IS NOT NULL order by CONT_RUT asc').createOrReplaceTempView("data_contador")
spark.sql('SELECT CONT_RUT from data_contador').createOrReplaceTempView("tiene_contador")
spark.sql('select tiene_contador.CONT_RUT as RUT_UNICO, CASE WHEN Valor IS NULL THEN "SOCIEDAD" ELSE "PERSONA"  END AS TIPO from tiene_contador left join naturales on tiene_contador.CONT_RUT=naturales.CONT_RUT').createOrReplaceTempView("tiene_contador")
spark.sql('SELECT DISTINCT RUT_CONTADOR as RUT_UNICO, "CONTADOR" AS TIPO FROM data_contador').createOrReplaceTempView("contadores")


# ## Construccion de relaciones de contadores

# In[ ]:


df_relaciones_contador=spark.sql('select CONT_RUT,RUT_CONTADOR, 0.25 as peso from data_contador WHERE CONT_RUT IS NOT NULL AND RUT_CONTADOR IS NOT NULL').toPandas()
df_relaciones_contador.to_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_contador.csv', index=False)


#  ## Unificacion de data de contadores con data de malla societaria

# In[ ]:


spark.sql('SELECT RUT_UNICO, TIPO FROM entidades UNION SELECT RUT_UNICO, TIPO FROM tiene_contador UNION SELECT RUT_UNICO, TIPO FROM contadores').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO, count(*) as c from entidades group by RUT_UNICO,TIPO').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO from entidades').createOrReplaceTempView("entidades")
# dejamos el label mas actual de cada nodo, en este caso se sobreescribe con el label 'contador'
# spark.sql('SELECT RUT_UNICO, CASE  WHEN COUNT(*) > 1 AND SUM(CASE WHEN TIPO = "CONTADOR" THEN 1 ELSE 0 END) > 0 THEN "CONTADOR" ELSE MAX(TIPO) END AS TIPO FROM  entidades GROUP BY RUT_UNICO').createOrReplaceTempView("entidades")


# ## Lectura de datos de representantes y definicion de tipos de RUT

# In[ ]:


spark.sql('SELECT repr_fecha_inicio_vo,cont_rut,cont_rut_representante,repr_fecha_termino_vo from dw.dw_trn_djr_representantes_e where cont_rut is not null and cont_rut_representante is not null order by cont_rut asc').createOrReplaceTempView("data_rep")
#filtramos los datos para seleccionar el representante o representantes vigentes el 2023
spark.sql('SELECT repr_fecha_inicio_vo,cont_rut,cont_rut_representante,repr_fecha_termino_vo  FROM  data_rep  WHERE  repr_fecha_inicio_vo < "2024-01-01" AND (repr_fecha_termino_vo IS NULL OR repr_fecha_termino_vo > "2023-01-01") order by repr_fecha_inicio_vo desc').createOrReplaceTempView("data_rep")
spark.sql('SELECT cont_rut as CONT_RUT,cont_rut_representante as CONT_RUT_REPRESENTANTE FROM  data_rep  ').createOrReplaceTempView("data_rep")


# In[ ]:


spark.sql('SELECT CONT_RUT from data_rep').createOrReplaceTempView("tiene_rep")
spark.sql('select tiene_rep.CONT_RUT as RUT_UNICO, CASE WHEN Valor IS NULL THEN "SOCIEDAD" ELSE "PERSONA"  END AS TIPO from tiene_rep left join naturales on tiene_rep.CONT_RUT=naturales.CONT_RUT').createOrReplaceTempView("tiene_rep")
spark.sql('SELECT DISTINCT CONT_RUT_REPRESENTANTE as RUT_UNICO, "REPRESENTANTE" AS TIPO FROM data_rep').createOrReplaceTempView("representantes")


# ## Unificacion de data de representantes con data de malla societaria

# In[ ]:


spark.sql('SELECT RUT_UNICO, TIPO FROM entidades UNION SELECT RUT_UNICO, TIPO FROM tiene_rep').createOrReplaceTempView("entidades1")
spark.sql('SELECT RUT_UNICO, TIPO FROM entidades1 UNION SELECT RUT_UNICO, TIPO FROM representantes').createOrReplaceTempView("entidades")


spark.sql('SELECT RUT_UNICO, TIPO, count(*) as c from entidades group by RUT_UNICO,TIPO').createOrReplaceTempView("entidades")
spark.sql('SELECT RUT_UNICO, TIPO from entidades').createOrReplaceTempView("entidades")
# dejamos el label mas actual de cada nodo, en este caso se sobreescribe con el label 'representante'
#spark.sql('SELECT RUT_UNICO, CASE  WHEN COUNT(*) > 1 AND SUM(CASE WHEN TIPO = "REPRESENTANTE" THEN 1 ELSE 0 END) > 0 THEN "REPRESENTANTE" ELSE MAX(TIPO) END AS TIPO FROM  entidades GROUP BY RUT_UNICO').createOrReplaceTempView("entidades")


# ## Construccion de relaciones de representantes

# In[ ]:


df_relaciones_representante=spark.sql('select *, 1 as peso from data_rep WHERE CONT_RUT IS NOT NULL AND CONT_RUT_REPRESENTANTE IS NOT NULL').toPandas()
df_relaciones_representante.to_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_representante.csv', index=False)


# ## Guardado en dataframe de pandas

# In[ ]:


entidades_def=spark.sql('select * from entidades where RUT_UNICO is not null order by RUT_UNICO asc')
entidades_def = entidades_def.groupBy("RUT_UNICO").pivot("TIPO").agg(lit(1)).fillna(0)
entidades_def.select('*').count()
entidades_def=entidades_def.withColumnRenamed("PERSONA", "NATURAL")


# ## Agregacion de informacion de la particion de grupos economicos ya establecidos

# In[ ]:


spark.read.parquet("abfs://data@datalakesii.dfs.core.windows.net/DatosOrigen/LibSDF/GE_APIUX_ARFI_E").createOrReplaceTempView("grupos_conocidos")
spark.sql('select PARU_RUT_E, COM, count(*) as c from grupos_conocidos  group by PARU_RUT_E, COM order by PARU_RUT_E asc').createOrReplaceTempView("grupos_conocidos")


# In[ ]:


entidades_def.createOrReplaceTempView("entidades_def")
spark.sql('select *, COM as COM_INICIAL from entidades_def left join grupos_conocidos on entidades_def.RUT_UNICO =grupos_conocidos.PARU_RUT_E').createOrReplaceTempView("grupos_final")
grupos_previos=spark.sql('select * from grupos_final')



# In[ ]:


grupos_previos=grupos_previos.select('RUT_UNICO','CONTADOR', 'NATURAL','REPRESENTANTE', 'SOCIEDAD','COM_INICIAL')


# In[ ]:


grupos_previos=grupos_previos.toPandas()
grupos_previos.to_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/nodos.csv', index=False)


# ## Guardar el diccionario con agrupacion previa como un archivo JSON

# In[ ]:


# Convertir a lista de diccionarios con orientación 'records'
grupos_previos_list = grupos_previos.fillna({'COM_INICIAL': 0}).to_dict(orient='records')

# Crear el diccionario con RUT_UNICO como clave y COM_INICIAL (con ceros donde sea nulo) como valor
grupos_previos_dict = {entry['RUT_UNICO']: entry['COM_INICIAL'] for entry in grupos_previos_list}

# Ruta del archivo
filepath = '/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/grupos_previos.json'

# Guardar la lista de diccionarios como JSON
with open(filepath, 'w') as file:
    json.dump(grupos_previos_dict, file)


# In[ ]:


spark.stop()


# In[ ]:




