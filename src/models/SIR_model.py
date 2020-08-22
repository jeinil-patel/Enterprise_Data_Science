import pandas as pd
import numpy as np

from scipy import optimize
from scipy.integrate import odeint

class SIR_Model():
    '''This class is programmed for SIR model of epidemiology
       Args:
       -------
       df: pd.DataFrame of large dataset
       country: select country
       population: total population of selected country
       percentage: percentage of total population which is susceptable
    '''
    
    def __init__(self, df, country, population, percentage=5):
        
        self.df = df
        self.country = country
        self.population = population
        self.percentage = percentage
        
        self._get_SIR_initials()
        
        
    def _calculate_susceptible(self):
        '''Calculation of total susceptable based on selected percentage'''
        self.N0 = (self.percentage/100)*self.population # max susceptible population, 10% of pupulation as default
    
    
    def _get_index(self, percentage):
        '''Day of initially infected population
        '''
        self._calculate_susceptible()
        self.idx_I0 = np.where(self.df[self.country] > self.N0*(percentage/100))[0][0]
        
        
    def _initial_infected(self, percentage=0.05):
        '''Initially infected population based on percentage.
           Args:
           ----
           percentage: user specified percentage
           Initially infected = Susceptable population * percentage(user-specified)
        '''
        self._get_index(percentage)
        self.ydata = np.array(self.df[self.country][self.idx_I0:])
        
        
    def _set_time(self):
        '''Set time period based on initially infected index
        '''
        self._initial_infected()
        self.t = np.arange(len(self.ydata))
        
    
    def _get_SIR_initials(self, R0=0):
        '''Set up initial values for SIR model.
           Recovery index is intially set to zero.
        '''
        self._set_time()
        self.I0 = self.ydata[0]
        self.S0 = self.N0-self.I0
        self.R0 = R0
        
        self.SIR = np.array([self.S0, self.I0, self.R0])
        
        
    def calculate_SIR(self, SIR, t, beta, gamma):
        ''' Simple SIR model
            S: susceptible population
            I: infected people
            R: recovered people
            beta: infection rate
            gamma: recovery rate
            t: time-step --> required for solving differential equation

            Overall condition is that the sum of changes (differnces) sum up to 0
            dS+dI+dR=0
            S+I+R= N (constant size of population)
        '''

        S,I,R = SIR
        dS_dt = -beta*S*I/self.N0          
        dI_dt = beta*S*I/self.N0 - gamma*I
        dR_dt = gamma*I

        return dS_dt, dI_dt, dR_dt
    
    def fit_odeint(self, x, beta, gamma):
        ''' Helper function for the integration
        '''
        self._get_SIR_initials()
        return odeint(self.calculate_SIR, (self.S0, self.I0, self.R0), self.t, args=(beta, gamma))[:,1]
    
    def fitted_curve(self, printout=True):
        '''Fitting of curve by using optimize.curve_fit form scipy libaray.
        '''
        self.popt, self.pcov = optimize.curve_fit(self.fit_odeint, self.t, self.ydata)
        self.perr = np.sqrt(np.diag(self.pcov))
        if printout:
            print('standard deviation errors : ',str(self.perr), ' start infect:',self.ydata[0])
            print("Optimal parameters: beta =", self.popt[0], " and gamma = ", self.popt[1])
        
        self.fitted = self.fit_odeint(self.t, *self.popt)
        # get the final fitted curve
        return self.fitted
    
def get_optimum_beta_gamma(df, country, susceptable_perc=5, period='default'):
    
    # get world population
    # plausiblization for dashboard
    try:
        df_population = pd.read_csv('../data/processed/world_population.csv',sep=';', index_col=0)
        population = df_population.T[country].values[0]
    except:
        df_population = pd.read_csv('data/processed/world_population.csv',sep=';', index_col=0)
        population = df_population.T[country].values[0]
    
    if period != 'default':
        # set periods
        periods = []
        periods.append([39,70])

        for i in np.arange(70,len(df)-1,period)[:-1]:
            periods.append([i, i+period])

        periods.append([np.arange(70,len(df)-1,period)[-1],len(df)-1])
        
        names = ['Period '+ str(n) for n in range(len(periods))]
        time_period = [str(df_confirmed.date[p[0]])[:10]+' to '+str(df_confirmed.date[p[1]])[:10] for p in periods]
        
    else:
        # rather than using fixed periods, we will use following periods for better approximation
        periods = [[39,70], [70,80], [80,100], [100,130], [130,180], [180,len(df)-1]]
        time_period = ['March 2020         ', 
                       '1-10th April 2020  ', 
                       '10-30th April 2020 ', 
                       'May 2020           ', 
                       'June-July 2020     ', 
                       'From August 2020   ']
        names = ['Virus spreaded          ', 
                 'People awared           ', 
                 'People take precautions ',
                 'Start recovering        ', 
                 'Constant spread         ', 
                 'Second wave             ']
    
    # fit curve
    fit_line = np.array([])
    dyn_beta = []
    dyn_gamma = []
    dyn_R0 = []
    summary = []
    for n, element in enumerate(periods):
        try:
            OBJ_SIR = SIR_Model(df[element[0]:element[1]], country= country, population = population, percentage=susceptable_perc)
            fit_line = np.concatenate([fit_line, OBJ_SIR.fitted_curve(printout=False)])
            dyn_beta.append(OBJ_SIR.popt[0])
            dyn_gamma.append(OBJ_SIR.popt[1])
            dyn_R0.append(OBJ_SIR.popt[0]/OBJ_SIR.popt[1])
        except:
            periods = periods[n+1:]
            dyn_beta.append(np.nan)
            dyn_gamma.append(np.nan)
            dyn_R0.append(np.nan)
            
        summary.append({'Time period':time_period[n], 
                        'Actions': names[n], 
                        'Beta': abs(round(dyn_beta[n],3)), 
                        'Gamma': abs(np.round(dyn_gamma[n],3)),
                        'R0': abs(np.round(dyn_R0[n],3))})
    
    # get strating point
    idx = SIR_Model(df, country= country, population = population).idx_I0
    
    return fit_line, idx, pd.DataFrame(summary)

if __name__ == '__main__':
    fit_line, idx, summary  = get_optimum_beta_gamma(df_confirmed, country='Germany', susceptable_perc=5)
    print(summary)