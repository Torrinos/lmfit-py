#!/usr/bin/env python

from lmfit import Parameters, Minimizer, calc_ci, calc_2dmap, minimize
import numpy as np
try:
    import pylab
    HASPYLAB = True
except ImportError:
    HASPYLAB = False

np.random.seed(1)

p_true = Parameters()
p_true.add('amp', value=14.0)
p_true.add('decay', value=0.010)
p_true.add('amp2', value=-10.0)
p_true.add('decay2', value=0.050)


def residual(pars, x, data=None):
    amp = pars['amp'].value
    decay = pars['decay'].value
    amp2 = pars['amp2'].value
    decay2 = pars['decay2'].value


    model = amp*np.exp(-x*decay)+amp2*np.exp(-x*decay2)
    if data is None:
        return model
    return (model - data)

n = 200
xmin = 0.
xmax = 250.0
noise = np.random.normal(scale=0.7215, size=n)
x     = np.linspace(xmin, xmax, n)
data  = residual(p_true, x) + noise

fit_params = Parameters()
fit_params.add('amp', value=14.0)
fit_params.add('decay', value=0.010)
fit_params.add('amp2', value=-10.0)
fit_params.add('decay2', value=0.050)

out = minimize(residual, fit_params, args=(x,), kws={'data':data})
out.leastsq()
ci, trace=calc_ci(out, trace_params=True)
for row in ci:    
    conv=lambda x: "%.5f" % x
    print("".join([row[0].rjust(10)]+[i.rjust(10) for i in map(conv,row[1:])]))

for row in ci:
    print out.params[row[0]].stderr, row[4]-row[3], row[3]-row[2]

pylab.plot(x,data)
pylab.figure()
names=fit_params.keys()
pylab.hot()

for i in range(4):
    for j in range(4):
        if i!=j:
            pylab.subplot(4,4,16-i*4-j)
            x,y,m=calc_2dmap(out,names[i],names[j],20,20)
            #print x,y,m
            pylab.contourf(x,y,m,20)
            pylab.xlabel(names[i])
            pylab.ylabel(names[j])
            
            x=trace[names[i]][names[i]]            
            y=trace[names[i]][names[j]]
            pr=trace[names[i]]['prob']
            s=np.argsort(x)
            pylab.plot(x[s],y[s],'g',lw=1)
            pylab.scatter(x[s],y[s],c=pr[s],s=30,lw=1)
        #print "jo"
#pylab.colorbar()
pylab.show()


    



