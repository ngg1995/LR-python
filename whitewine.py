import pandas as pd
import numpy as np
import random
from matplotlib import pyplot as plt
from sklearn.linear_model import LogisticRegression
import itertools as it
from tqdm import tqdm
import pba

from LRF import *

def intervalise(val,eps,method='u',b=0.5,bounds = None):
    
    if method == 'u':
        m = np.random.uniform(val-eps,val+eps)
    elif method == 't':
        m = np.random.triangular(val-eps,val-b*eps,val+eps)
    
    if bounds is not None:
        if m-eps < bounds[0]:
            return pba.I(bounds[0],m+eps)
        elif m+eps >bounds[1]:
            return pba.I(m-eps,bounds[1])
        
    return pba.I(m-eps,m+eps)


def midpoints(data):
    n_data = data.copy()
    for c in data.columns:
        for i in data.index:
            if data.loc[i,c].__class__.__name__ == 'Interval':
                n_data.loc[i,c] = data.loc[i,c].midpoint()
            
    return n_data

    
# Import the data
wine_data = pd.read_csv('winequality-white.csv',index_col = None)

# Split the data into test/train factors and result
random.seed(1111) # for reproducability

train_data_index = random.sample([i for i in wine_data[wine_data['quality'] <= 6].index], k = 50) + random.sample([i for i in wine_data[wine_data['quality'] >= 7].index ], k = 50)
test_data_index = [i for i in wine_data.index if i not in train_data_index]

test_data = wine_data.loc[test_data_index,[c for c in wine_data.columns if c != 'quality']]
train_data = wine_data.loc[train_data_index,[c for c in wine_data.columns if c != 'quality']]

test_results = wine_data.loc[test_data_index,'quality'] >= 7
train_results = wine_data.loc[train_data_index,'quality'] >= 7

# Intervalise data
eps = {"fixed acidity":(0.2,'u'),
       "volatile acidity":(0.05,'t'),
       "citric acid":(0.03,'t',-0.75),
       "residual sugar":(0.02,'u'),
       "chlorides":(0.003,'u'),
       "free sulfur dioxide":(2,'u'),
       "total sulfur dioxide":(2,'u'),
       "density":(0.01,'t',0.9,(0,1)),
       "pH":(.01,'t'),
       "sulphates":(0.01,'t'),
       "alcohol":(0.1,'t')
       }

np.random.seed(0)
UQdata = pd.DataFrame({
    **{k:[intervalise(train_data.loc[i,k],*eps[k]) for i in train_data.index] for k, e in eps.items()},
    **{c:train_data[c] for c in train_data.columns if c not in eps.keys()}
    }, dtype = 'O')

### Fit logistic regression model on full dataset
base = LogisticRegression(max_iter=1000)
base.fit(train_data.to_numpy(),train_results.to_numpy())


### Fit models with midpoint data
nuq_data = midpoints(UQdata)
nuq = LogisticRegression(max_iter=1000)
nuq.fit(nuq_data.to_numpy(),train_results.to_numpy())

### Fit UQ models
uq_models = int_logistic_regression(UQdata,train_results)

### Get confusion matrix
# Classify test data
base_predict = base.predict(test_data)

# CLASSIFY NO_UQ MODEL DATA 
nuq_predict = nuq.predict(test_data)

# CLASSIFY UQ MODEL 
test_predict = pd.DataFrame(columns = uq_models.keys())

for key, model in uq_models.items():
    test_predict[key] = model.predict(test_data)
    
predictions = []
for i in test_predict.index:
    predictions.append([min(test_predict.loc[i]),max(test_predict.loc[i])])

with open('runinfo/whitewine_cm.out','w') as f:
    print('TRUE MODEL',file = f)
    a,b,c,d = generate_confusion_matrix(test_results,base_predict)
    print('TP=%i\tFP=%i\nFN=%i\tTN=%i' %(a,b,c,d),file = f)

    # Calculate sensitivity and specificity
    print('Sensitivity = %.3f' %(a/(a+c)),file = f)
    print('Specificity = %.3f' %(d/(b+d)),file = f)

    print('DISCARDED DATA MODEL',file = f)
    aa,bb,cc,dd = generate_confusion_matrix(test_results,nuq_predict)
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
    print('Sensitivity = %.3f' %(ss),file = f)
    print('Specificity = %.3f' %(tt),file = f)
    
    print('UQ MODEL',file = f)
    
    aaai,bbbi,ccci,dddi = generate_confusion_matrix(test_results,predictions,throw = False)
    try:
        sssi = 1/(1+ccci/aaai)
    except:
        sssi = None
    try:    
        ttti = 1/(1+bbbi/dddi)
    except:
        ttti = None
        
    print('TP=%s\tFP=%s\nFN=%s\tTN=%s' %(aaai,bbbi,ccci,dddi),file = f)

    # Calculate sensitivity and specificity
    print('Sensitivity = %s' %(sssi),file = f)
    print('Specificity = %s' %(ttti),file = f)

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

### ROC CURVE
s,fpr = ROC(model = base, data = test_data, results = test_results)
nuq_s,nuq_fpr = ROC(model = nuq, data = test_data, results = test_results)
s_t, fpr_t, Sigma, Tau, Nu = UQ_ROC_alt(uq_models, test_data, test_results)

s_i, fpr_i = UQ_ROC(uq_models, test_data, test_results)

steps = 1000
X = np.linspace(0,1,steps)
Ymin = steps*[2]
Ymax = steps*[-1]

for i, x in tqdm(enumerate(X)):
    for k,j in zip(s_i,fpr_i):

        if j.straddles(x,endpoints = True):
            Ymin[i] = min((Ymin[i],k.Left))
            Ymax[i] = max((Ymax[i],k.Right))

Xmax = [0]+[x for i,x in enumerate(X) if Ymax[i] != -1]+[1]
Xmin = [0]+[x for i,x in enumerate(X) if Ymin[i] != 2]+[1]
Ymax = [0]+[y for i,y in enumerate(Ymax) if Ymax[i] != -1]+[1]
Ymin = [0]+[y for i,y in enumerate(Ymin) if Ymin[i] != 2]+[1]

auc_int_min = sum([(Xmin[i]-Xmin[i-1])*Ymin[i] for i in range(1,len(Xmin))])
auc_int_max = sum([(Xmax[i]-Xmax[i-1])*Ymax[i] for i in range(1,len(Xmin))])
   
plt.xlabel('$1-t$')
plt.ylabel('$s$')
plt.step(fpr,s,'k', label = 'Base')
plt.step(nuq_fpr,nuq_s,'m', label = 'Discarded')
plt.step(fpr_t,s_t,'y', label = 'Not Predicting')
plt.plot(Xmax,Ymax,'r',label = 'Interval Bounds')
plt.plot(Xmin,Ymin,'r')

plt.legend()

plt.savefig('figs/whitewine_ROC.png',dpi = 600)
plt.savefig('../paper/figs/whitewine_ROC.png',dpi = 600)
plt.clf()

with open('runinfo/whitewine_auc.out','w') as f:
    print('NO UNCERTAINTY: %.4f' %auc(s,fpr), file = f)
    print('DISCARDED: %.4F' %auc(nuq_s,nuq_fpr),file = f)
    print('THROW: %.4f' %auc(s_t,fpr_t), file = f)
    print('INTERVALS: [%.4f,%.4f]' %(auc_int_min,auc_int_max), file = f)
    

fig = plt.figure()

ax = plt.axes(projection='3d',elev = 45,azim = -45,proj_type = 'ortho')
ax.set_xlabel('$1-t$')
ax.set_ylabel('$s$')
# ax.set_zlabel('$1-\sigma,1-\\tau$')
ax.plot(fpr_t,s_t,'m',alpha = 0.5)
ax.plot3D(fpr,s,Sigma,'b',label = '$\\sigma$')
ax.plot3D(fpr,s,Tau,'r',label = '$\\tau$')
# ax.plot3D(fpr,s,Nu,'k',label = '$1-\\nu$')

ax.legend()

plt.savefig('figs/whitewine_ROC3D.png',dpi = 600)
plt.savefig('../paper/figs/whitewine_ROC3D.png',dpi = 600)

### Hosmer-Lemeshow
hl_b, pval_b = hosmer_lemeshow_test(base,train_data,train_results,Q = 20)

hl_nuq, pval_nuq = hosmer_lemeshow_test(nuq,train_data,train_results,Q = 20)

hl_min = np.inf
hl_max = 0
pval_max = 0
pval_min = 1

for k,m in uq_models.items():
    hl_,pval_ = hosmer_lemeshow_test(m,train_data,train_results,Q = 10)
    hl_min = min(hl_min,hl_)
    pval_min = min(pval_min,pval_)
    
    hl_max = max(hl_max,hl_)
    pval_max = max(pval_max,pval_)
    
    
with open('runinfo/whitewine_HL.out','w') as f:
    print('base\nhl = %.3f, p = %.5f' %(hl_b,pval_b),file = f)
    print('no UQ\nhl = %.3f, p = %.5f' %(hl_nuq,pval_nuq),file = f) 

    print('UQ\nhl = [%.3f,%.3f], p = [%.5f,%.5f]' %(hl_min,hl_max,pval_min,pval_max),file = f) 