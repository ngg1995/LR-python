import pandas as pd
import numpy as np
import random
from matplotlib import pyplot as plt
from sklearn.linear_model import LogisticRegression
import itertools as it
from tqdm import tqdm
import pba
from LRF import *
                  
# Import the data
heart_data = pd.read_csv('SAheart.csv',index_col = 'patient')

# Split the data into risk factors and result
factors = heart_data[['sbp','tobacco','ldl','adiposity','famhist','typea','obesity','alcohol','age']]
chd = heart_data['chd']

test_data, test_results, train_data, train_results, uq_data = split_data(factors,chd,test_frac = 0.3,uq_frac=0.03,seed = 2)

# Fit model
base = LogisticRegression(max_iter=500)
base.fit(train_data, train_results)

# Make preictions from test data
base_predict = base.predict(test_data)

# Make prediction for uncertain data 
uq_models = uc_logistic_regression(train_data, train_results, uq_data)

test_predict = pd.DataFrame(columns = uq_models.keys())

for key, model in uq_models.items():
    test_predict[key] = model.predict(test_data)
    
predictions = []
for i in test_predict.index:
    predictions.append([min(test_predict.loc[i]),max(test_predict.loc[i])])

## Get confusion matrix
with open('heart-cm.out','w') as f:
    a,b,c,d = generate_confusion_matrix(test_results,base_predict)
    print('TP=%i\tFP=%i\nFN=%i\tTN=%i' %(a,b,c,d),file = f)

    # Calculate sensitivity and specificity
    print('Sensitivity = %.3f' %(a/(a+c)),file = f)
    print('Specificity = %.3f' %(d/(b+d)),file = f)


    aa,bb,cc,dd = generate_confusion_matrix(test_results,predictions)
    try:
        ss = 1/(1+cc/aa)
    except:
        ss = None
    try:    
        tt = 1/(1+bb/dd)
    except:
        tt = None
    print('TP=%s\tFP=%s\nFN=%s\tTN=%s' %(aa,bb,cc,dd),file = f)

    # Calculate sensitivity and specificity
    print('Sensitivity = %s' %(ss),file = f)
    print('Specificity = %s' %(tt),file = f)

    aaa,bbb,ccc,ddd,eee,fff = generate_confusion_matrix(test_results,predictions,throw = True)
    try:
        sss = 1/(1+ccc/aaa)
    except:
        sss = None
    try:    
        ttt = 1/(1+bbb/ddd)
    except:
        ttt = None
        
    print('TP=%i\tFP=%i\nFN=%i\tTN=%i\nNP(+)=%i\tNP(-)=%i' %(aaa,bbb,ccc,ddd,eee,fff),file = f)

    # Calculate sensitivity and specificity
    print('Sensitivity = %.3f' %(sss),file = f)
    print('Specificity = %.3f' %(ttt),file = f)

## ROC CURVE
s,fpr = ROC(model = base, data = test_data, results = test_results)
s_lb, fpr_lb, s_ub, fpr_ub = UQ_ROC(models = uq_models, data = test_data, results = test_results)

plt.plot([0,1],[0,1],'k:')
plt.xlabel('1-$t$')
plt.ylabel('$s$')
plt.plot(fpr,s,'r')
plt.savefig('figs/heart_ROC.png')
plt.plot(fpr_lb,s_lb,'g')
plt.plot(fpr_ub,s_ub,'k')
# print(len(fpr))
plt.savefig('figs/heart_ROC_UQ.png')

plt.clf()
## PLOTS

l = len(train_data.columns)
colors = ['g' if d else 'r' for c,d in train_results.iteritems()]
for i,(j,k) in enumerate(it.product(train_data.columns,repeat=2)):
    if j != k:
        plt.subplot(l,l,i+1)
        plt.scatter(train_data[j],train_data[k],c=colors)
        plt.scatter(uq_data[j],uq_data[k],c='k')
        
plt.savefig('figs/heart.png')