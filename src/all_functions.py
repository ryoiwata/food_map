#Serializing to a file
import _pickle as pickle

#Libraries for Graph
import networkx as nx

#Python Library for Dataframe usage
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import random
from collections import Counter
from itertools import combinations
import math

#PandaDF of ingredients and their associated flavor molecules
#Opening the pickled file
pickle_in = open("./data/pandas/flavorDB_pandas.pickle", "rb")
#Getting the PandaDF from the pickle
ingredient_only_pd = pickle.load(pickle_in)

#PandaDF of ingredients and their associated flavor molecules
#Opening the pickled file
pickle_in = open("./data/pandas/recipe_puppy_pandas.pickle", "rb")
#Getting the PandaDF from the pickle
recipe_puppy_pandas = pickle.load(pickle_in)


"""
#accessing mongoDB for flavor molecules
client = MongoClient()
database = client['food_map']   # Database name (to connect to)
collections_molecule = database['flavor_molecules']
collections_recipe = database['recipes']
#Getting the dataset from MongoDB into Pandas for recipes
recipe_puppy_pandas = pd.DataFrame(list(collections_recipe.find()))
recipe_puppy_pandas = recipe_puppy_pandas.drop_duplicates(subset= "recipe_name", keep="last")
"""




"""
GRAPH CREATION
"""

def graph_based_on_shared_recipe_creator(pandas_df = recipe_puppy_pandas):
    #dropping duplicates before using pandas_df as a graph
    pandas_df = pandas_df.drop_duplicates(subset= "recipe_name", keep="last")
    number_of_recipes = 0
            

    #Initializing the Graph
    G=nx.Graph()

    #iterate through each recipe
    for index, row in pandas_df.iterrows():
        ingredient_list = set(row["recipe_ingredients"])
        if len(ingredient_list) <= 1:
            continue
        number_of_recipes += 1

        for ingredient in ingredient_list:

            if ingredient not in G:
                category = ingredient_only_pd.loc[ingredient_only_pd['ingredient'] == ingredient, 'category'].values[0]
                G.add_node(ingredient)
                G.node[ingredient]["ingredient_node"] = True
                G.node[ingredient]["molecule_node"] = False
                G.node[ingredient]["category"] = category
                G.node[ingredient]["quantity"] = 1

            else:
                G.node[ingredient]["quantity"] += 1


        #generator of all the pairs of ingredients within a recipe
        for combo in combinations(ingredient_list, 2):
            
            #individual ingredient from the combonitation
            ingredient_1 = combo[0]
            ingredient_2 = combo[1]

            if str(ingredient_1) == str(ingredient_2):
                continue

            #Adding edges if an ingredient is within the same recipe
            if G.get_edge_data(ingredient_1, ingredient_2) == None:
                G.add_edge(ingredient_1, ingredient_2, weight = 1)
            else:
                G[ingredient_1][ingredient_2]["weight"] += 1
    
    for edge in G.edges():
        ingredient_1 = edge[0]
        prob_ing_1 = G.node[ingredient_1]["quantity"] / number_of_recipes
        # print(ingredient_1, prob_ing_1)

        ingredient_2 = edge[1]
        prob_ing_2 = G.node[ingredient_2]["quantity"] / number_of_recipes
        # print(ingredient_2, prob_ing_2)

        original_edge_weight = G[ingredient_1][ingredient_2]["weight"]
        prob_ing_1_and_ing_2 = original_edge_weight / number_of_recipes
        # print(ingredient_1, ingredient_2, prob_ing_1_and_ing_2)

        G[ingredient_1][ingredient_2]["pmi"] = math.log10( prob_ing_1_and_ing_2 / (prob_ing_1 * prob_ing_2) )
        G[ingredient_1][ingredient_2]["iou"] = G[ingredient_1][ingredient_2]["weight"] / (G.node[ingredient_1]["quantity"] + G.node[ingredient_2]["quantity"])


    return G

def graph_based_on_ingredient_with_associated_flavor_molecule_creator(pandas_df = ingredient_only_pd):
    #Initializing Graph
    G=nx.Graph()

    #iterate through each row of flavorDB based on if index is in random sample
    for index, row in pandas_df.iterrows():

        #name of the ingredient from the "rows" 
        ingredient = row["ingredient"]
        #category of the ingredient from the "rows"
        category = row["category"]
        #set of the ingredient from the "rows"
        set_of_molecules= row["set_molecules"]

        #creating an ingredient node and adding attributes
        G.add_node(ingredient)
        G.node[ingredient]["ingredient_node"] = True
        G.node[ingredient]["molecule_node"] = False
        G.node[ingredient]["category"] = category

        # to keep track of what's going on
        for molecule in set_of_molecules:           
            #creating a molecule node and adding attribute
            G.add_node(molecule)
            G.node[molecule]["molecule_node"] = True
            G.node[molecule]["ingredient_node"] = False
            G.add_edge(ingredient, molecule)
    return G



def graph_based_on_shared_molecule_creator(pandas_df = ingredient_only_pd, min_intersection_ratio = 0.5):
    #Initializing Graph
    G=nx.Graph()

    #iterate through each row of flavorDB 
    for index, row1 in pandas_df.iterrows():
        #ingredient name
        ingredient = row1["ingredient"]
        #ingredient category
        category_1 = row1["category"]
        #ingredient molecules
        molecules_1 = row1["set_molecules"]

        #creating an ingredient node and adding attributes
        G.add_node(ingredient)
        G.node[ingredient]["ingredient_node"] = True
        G.node[ingredient]["molecule_node"] = False
        G.node[ingredient]["category"] = category_1

        for index, row2 in pandas_df.iterrows():
            #ingredient name
            ingredient_2 = row2["ingredient"]
            
            #checks to see if ingredients are different
            if ingredient != ingredient_2:
                #ingredient category
                category_2 = row2["category"]
                #ingredient molecules
                molecules_2 = row2["set_molecules"]
                
                #creating an ingredient node and adding attributes
                G.add_node(ingredient_2)
                G.node[ingredient_2]["ingredient_node"] = True
                G.node[ingredient_2]["molecule_node"] = False
                G.node[ingredient_2]["category"] = category_2
                
                #quantifying the number of molecules in each ingredient, 
                #and finding the intersection of the two
                num_intersection = len(molecules_1.intersection(molecules_2))
                total_molecules = len(molecules_1.union(molecules_2))
                intersection_ratio = num_intersection / total_molecules

                #creating an edge if the two ingredients
                #have at least a minimum ratio of intersection 
                if intersection_ratio > min_intersection_ratio:
                    G.add_edge(ingredient, ingredient_2, weight=intersection_ratio)
    return G

"""
ANALYSIS
"""

def common_pair_analysis(ing1, ing2, pandas_df = ingredient_only_pd, graph_it = False, print_statements = False):
    demo_G=nx.Graph()
    mol_list = []
    #iterate through each row of flavorDB based on if index is in random sample
    for index, row in pandas_df.iterrows():
        #set of the ingredient from the "rows"
        set_mol= row["set_molecules"]
        #name of the ingredient from the "rows" 
        ingredient = row["ingredient"]

        if ingredient in [ing1, ing2]:
            mol_list.append(set_mol)
            for molecule in set_mol:
                demo_G.add_node(ingredient)
                demo_G.node[ingredient]["ingredient_node"] = True
                demo_G.add_node(molecule)
                demo_G.node[molecule]["molecule_node"] = True
                demo_G.add_edge(ingredient, molecule)
    ingredient_nodes = nx.get_node_attributes(demo_G, 'ingredient_node').keys()
    molecule_nodes = nx.get_node_attributes(demo_G, 'molecule_node').keys()
    pos=nx.spring_layout(demo_G)
    if graph_it == True:
        nx.draw_networkx_nodes(demo_G,pos,
                            nodelist=ingredient_nodes,
                            node_color='r',
                            node_size=500,
                        alpha=0.8)
        nx.draw_networkx_nodes(demo_G,pos,
                            nodelist=molecule_nodes,
                            node_color='b',
                            node_size=500,
                        alpha=0.8)
    
    shared_molecules = mol_list[0].intersection(mol_list[1])
    mol_for_ing_1 = mol_list[0].difference(mol_list[1])
    mol_for_ing_2 = mol_list[1].difference(mol_list[0])
    
    ratio_shared_to_total = len(shared_molecules) / len(mol_list[1].union(mol_list[0]))
    num_unique_molecules_1 = len(mol_for_ing_1)
    num_unique_molecules_2 = len(mol_for_ing_2)
    num_shared_molecules = len(shared_molecules)    
    if print_statements == True:
        print("number of shared molecules: ", num_shared_molecules)
        print("number of unique molecules to {}: ".format(ing1), len(mol_for_ing_1))
        print("number of unique molecules to {}: ".format(ing2), len(mol_for_ing_2))
        print("ratio of shared to total: ", ratio_shared_to_total)
    return ratio_shared_to_total, num_unique_molecules_1, num_unique_molecules_2, num_shared_molecules

if __name__ == "__main__":
    pass