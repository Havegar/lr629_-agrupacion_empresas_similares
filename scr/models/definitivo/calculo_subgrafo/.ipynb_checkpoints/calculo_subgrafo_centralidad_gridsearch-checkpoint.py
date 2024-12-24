import networkx as nx
import pandas as pd
import json
import random
import igraph as ig

# ## Carga de datos a utilizar

df_relaciones_malla = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_malla_societaria.csv')
df_relaciones_contador = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_contador.csv')
df_relaciones_representante = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_representante.csv')
df_relaciones_familiares = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/relaciones_familiares.csv')
df_entidades = pd.read_csv('/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/nodos.csv')

# ## Grupos iniciales de contribuyentes

ruta_archivo = '/home/cdsw/data/processed/nodos_relaciones_pregrupos_for_louvain/grupos_previos.json'
with open(ruta_archivo, 'r') as archivo:
    grupos_previos = json.load(archivo)

# ## Creacion del grafo y carga de relaciones

G = nx.Graph()

# Cargamos relaciones de diferentes fuentes y las añadimos al grafo
for _, row in df_relaciones_malla.iterrows():
    G.add_node(row['RUT_SOCIEDAD'])
    G.add_node(row['RUT_SOCIO'])
    G.add_edge(row['RUT_SOCIEDAD'], row['RUT_SOCIO'], weight=row['peso'])

for _, row in df_relaciones_contador.iterrows():
    G.add_node(row['CONT_RUT'])
    G.add_node(row['RUT_CONTADOR'])
    G.add_edge(row['CONT_RUT'], row['RUT_CONTADOR'], weight=row['peso'])

for _, row in df_relaciones_representante.iterrows():
    G.add_node(row['CONT_RUT'])
    G.add_node(row['CONT_RUT_REPRESENTANTE'])
    G.add_edge(row['CONT_RUT'], row['CONT_RUT_REPRESENTANTE'], weight=row['peso'])

for _, row in df_relaciones_familiares.iterrows():
    G.add_node(row['CONT_RUT'])
    G.add_node(row['RUT_FAM'])
    G.add_edge(row['CONT_RUT'], row['RUT_FAM'], weight=row['peso'])

# ## Seleccionar el 10% de entidades de cada comunidad inicial

degree_centrality = nx.degree_centrality(G)

sorted_nodes = sorted(degree_centrality, key=degree_centrality.get, reverse=True)

top_percent = 0.1

num_top_nodes = int(len(sorted_nodes) * top_percent)

top_nodes = sorted_nodes[:num_top_nodes]

subgraph = G.subgraph(top_nodes)

subgraph_nodes = list(subgraph.nodes())

G_sub_igraph = ig.Graph.TupleList(subgraph.edges(), directed=False)

num_nodes_subgraph = len(G_sub_igraph.vs)

print(f"Number of nodes in the subgraph: {num_nodes_subgraph}")

subgraph_nodes_set = set(subgraph_nodes)

diccionario_grupos_muestra = {rut: grupos_previos[rut] for rut in subgraph_nodes_set if rut in grupos_previos}

subgraph_nodes = G_sub_igraph.vs['name']

membership = [grupos_previos.get(node, 0) for node in subgraph_nodes]

print(f"Length of the membership list: {len(membership)}")

assert len(membership) == num_nodes_subgraph, "Membership list length does not match the number of nodes in the subgraph."

# Guardar el subgrafo en un archivo GraphML
nx.write_graphml(subgraph, "/home/cdsw/data/processed/subgrafo/muestreo_centralidad/subgraph_filtrado.graphml")

with open('/home/cdsw/data/processed/subgrafo/muestreo_centralidad/membership.json', 'w') as json_file:
    json.dump(membership, json_file)
    
with open('/home/cdsw/data/processed/subgrafo/muestreo_centralidad/diccionario_grupos_muestra.json', 'w') as json_file:
    json.dump(diccionario_grupos_muestra, json_file)
    
   



