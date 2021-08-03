from pandas import DataFrame
import pandas as pd
import operator
import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel
import sys
from flask import Flask, render_template , request
from flask_restful import Api,Resource
from mysql.connector import connect
import types
import numpy
import json

courseIncrement=0
totalRecords=0
mylist = {}
coursecount=0



def get_mysql_db_connection():
    db_details = {'host':'10.42.206.2',
                  'user':'zentalentdev',
                  'password':'3k2@M5t6',
                  'database':'ZenTalent'}
    con = connect(**db_details)
    return con


#sql = """select count(*) from ZenLearnCourseMasterView where itemTitle is not null and itemTitle!='' """
sql = """select count(*) from zenlearncoursedictionary """
con = get_mysql_db_connection()
cursor = con.cursor()
cursor.execute(sql)
totalRecords = cursor.fetchone()
con.close()
totalRecords = int(''.join(map(str,totalRecords)))
print(totalRecords)

sql="""select trim(itemTitle),trim(id) from ZenLearnCourseMasterView where itemTitle is not null and itemTitle!='' and recordprocessed=0 """
con = get_mysql_db_connection()
cursor = con.cursor()
cursor.execute(sql)
z = cursor.fetchall()

con.close()
if len(z)<=0:
    exit("******No records to process******")
df_of_cou = DataFrame(z)
df_of_cou = DataFrame(z, columns=['itemTitle', 'id'])

def give_recommandation(title,coursemasterid, sig,indice,df):
    global coursecount
    global mylist
    print()
    print('In give_recommandation() method')
    try:
        print(title)
        idx = indice[title]
        if type(idx) is numpy.int64:
            idx=idx
        else:
            idx=idx[0]
        print(type(idx))
        sig_scores = list(enumerate(sig[idx]))
        # sort
        sig_scores = sorted(sig_scores, key=lambda a: a[1], reverse=True)

        for i in sig_scores:
            mylist[str(df['id'].loc[i[0]])]=i[1]

    except Exception as e:
        print("Key not found")
        print(e.__cause__)
        return 1



def recommendation_on_learning_history(sig,indice,df,title,id):
    global coursecount
    try:
        a = give_recommandation(title,id, sig, indice, df)
        if a == 1:
            coursecount = coursecount + 1
        return a
    except Exception as e:
        print('exception occured')
        print(e)


def recommendation_logic(start,end,title,id):
    try:
        sql = """ select trim(itemtitle),trim(dictionaryid) from zenlearncoursedictionary limit %s,%s union select trim(itemTitle),trim(id) from ZenLearnCourseMasterView where trim(itemTitle)= %s """
        print(sql)
        con= get_mysql_db_connection()
        cursor = con.cursor()
        val = (start,end,title)
        cursor.execute(sql,val)
        x = cursor.fetchall()
        con.close()
        df = DataFrame(x)
        df = DataFrame(x, columns=['itemTitle','id'])
        df['itemTitle'] = df['itemTitle'].astype(str)
        tfv = TfidfVectorizer(strip_accents='unicode', analyzer='word', token_pattern=r'\w{1,}',
                      ngram_range=(1, 3), stop_words='english')
        df['itemTitle'] = df['itemTitle'].fillna('')
        tfv_matrix = tfv.fit_transform(df['itemTitle'])
        sig = sigmoid_kernel(tfv_matrix, tfv_matrix)
        indice = pd.Series(df.index, index=df['itemTitle']).drop_duplicates()
        result = recommendation_on_learning_history(sig, indice, df,title,id)
    except Exception as e:
        print(e)
    return result
#insertScoreData(int(str(id)), int(str(key)),str(value),con)
def insertScoreData(coursemasterid,dictionaryid,score,con):
    try:
        sql = """insert into zenlearnrecommendationscores_copy(dictionaryid,coursemasterid,score) values(%s,%s,%s)"""
        #sql = """insert into zenlearnrecommendationscores_copy_copy(dictionaryid,coursemasterid,score) values(%s,%s,%s)"""
        val=(dictionaryid,coursemasterid,score)
        cursor = con.cursor()
        result=cursor.execute(sql,val)

    except Exception as e:
        print(e)
    return 1
#counter = 0
for ind in df_of_cou.index:
    itemtitle=df_of_cou['itemTitle'][ind]
    id=df_of_cou['id'][ind]
    print(itemtitle)
    print(id)
    finalResultList = []
    while totalRecords > courseIncrement:
        recommendation_logic(courseIncrement, 20000,itemtitle,str(id))
        courseIncrement = courseIncrement + 20000
    courseIncrement = 0
    sorted_d = dict(sorted(mylist.items(), key=operator.itemgetter(1), reverse=True))
    c = 1
    con = get_mysql_db_connection()
    for key, value in sorted_d.items():
        print(key, '->', value)
        if int(str(id))!= int(str(key)):
            insertScoreData(int(str(id)), int(str(key)),str(value),con)
            c = c + 1
            if c >= 200:
                break
    sql = """update ZenLearnCourseMaster set recordprocessed=1 where id=%s"""
    val = (int(str(id)),)
    cursor = con.cursor()
    result = cursor.execute(sql, val)
    con.commit()
    con.close()
    mylist= {}
 #   counter= counter + 1
 #   if counter >=2:
 #       break

print('****Successfully completed the process****')

