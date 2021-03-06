import numpy as np
import matplotlib.pyplot as plt

##########################
#### Global Variables ####
##########################
#mainly used by functions as initial conditions/constants

#years will be by default -- 2021 to 2030 (defined in function)

#For determining Energy -- increase in MWhr / year -- default 6.92*10**6 (defined in function)

#### inital conditions for determining percentages ####
#format for arrays is [<Coal>, <Natural Gas>, <Solar>, <Wind>, <Nuclear>, <Winter NG>]
initial_percentages = np.array([19.3, 53.6, 0.9, 17.5, 8.7, 0])

derivative_sources = np.array([-1.89, 0, 0.0976, 1.29, -0.116, 0])
#note - NG will be taken as slack in calculation, so value is NA
#rate for winter NG is zero by default

#sec_derivative_sources = all zeros by default (defined in function) i.e., np.zeros(6)

#### values needed for reliability ####
#reliability scores for each source based on 2021
aRelScores = np.array([-9192.435233, -5811.753731, 26687.77778, -5368.914286, -8413.448276, 0])

#Percent Effectiveness of winterized NG -- 83.5 (defined as default in function)

#construction costs per kW in USD
const_costs = np.array([3500, 895, 2436, 1630, 5945, 899])
#kW increase in energy each year to calculate costs -- 789954.3379kW


#To determine consumer costs --- (cents/kWh) per 1% source
gen_costs = np.array([0.05230569948, 0.05229477612, 0.05233333333, 0.05228571429, 0.05229885057, 0.05229477612])
non_gen_costs = np.array([0.08514812774, 0.02177359266, 0.0592630969, 0.03965469949, 0.144630177, 0.02187004968])


#emissions in Million Metric Tons per 1% source per MWh
source_emissions = np.array([1.0170164*10**-8, 1.008*10**-8, 0, 0, 0, 1.008*10**-8])

###################
#### Functions ####
###################
#naming convention -- mix of underscore and camal case
#array/matrix indicated by "a" followed by the the quantity in camal case


def get_aYear(start_year=2021, end_year=2030, size=1000):
    '''returns an array for the time in years with default of 1000 samples'''
    return np.linspace(start_year, end_year, size)


def get_aEnergy(aYear, dirE=6.92*10**6):
    '''returns an array for the energy production each year, uses default slope from trendline'''
    #use formula generate array
    aEnergy = dirE*aYear - 1.35*10**10
    return aEnergy


def get_aPercentSources(aYear, initial_percentages=initial_percentages, derivative_sources=derivative_sources, sec_derivative_sources=np.zeros(6)):
    '''returns a matrix for the percentages of the 6 sources (coal, NG, solar, wind, nuclear, winter NG), based on years and initial conditions
    initial conditions are by default: 2nd derivative set to zero, inital percentages from 2019, 1st derivatives from linear trends'''
    size = (len(aYear),6) #size will be matrix with rows equal to samples in years, columns for each source
    aPercentSources = np.zeros(size) #initalize matrix
    P = initial_percentages #initalize sub-array which will be used calculate percentages in each row
    
    #interatve over all time samples in aYear
    for i in range(len(aYear)):
        #determine sub-array value
        P = sec_derivative_sources*(0.5*(aYear[i]-2021)**2) + derivative_sources*(aYear[i]-2021) + initial_percentages
        
        #set any percentages to zero if they have gone negative, skip NG
        if P[0] < 0:
            P[0] = 0
        if P[2] < 0:
            P[2] = 0
        if P[3] < 0:
            P[3] = 0
        if P[4] < 0:
            P[4] = 0
        if P[5] < 0:
            P[5] = 0

        #print(P)
        #determine NG perc. as slack
        NG = 100-(P[0]+P[2]+P[3]+P[4]+P[5])

        #check if percentage for NG will stay positive, if so, assign P and NG to aPercentSources
        if NG >= 0:
            aPercentSources[i,:] = P
            aPercentSources[i,1] = NG

        else: #if NG ends up being negative, set this row to previous value (i.e. keep P constant)
            if i > 0: #check to make sure that this isn't the 1st index
                aPercentSources[i,:] = aPercentSources[i-1,:]
            
            else: #first index
                aPercentSources[i,:] = initial_percentages
        
        #print(aPercentSources[i,:])
    
    return aPercentSources
        


def get_aReliability(aYear, aPercentSources, aEnergy, perc_effective=83.5, dirE=6.92*10**6, aRelScores=aRelScores):
    '''returns array for the reliability score for a given set of years, energy production, and percent distribution of sources'''
    aReliability = np.zeros(len(aYear)) #initalize reliability array
    Energy_2021 = dirE*2021 - 1.35*10**10 #determine annual energy for 2021 (needed later for calc)
    #determine reliability score for winterized NG
    aRelScores[5] = (1-perc_effective/100)*aReliability[1]

    #determine scale factor for energy production as array
    u = aEnergy/Energy_2021

    #iterate over all samples in aYear
    for i in range(len(aYear)):
        aReliability[i] = u[i]*np.dot(aRelScores, aPercentSources[i,:])
        
    return aReliability

def get_aConstructionCost(aYear, aPercentSources, const_costs=const_costs, rateE_kW=789954.3379):
    '''returns an array for the annual construction cost based on years, percent source distribution, construction cost, and rate of increase in energy production'''
    aConstructionCost = np.zeros(len(aYear)) #initalize array for costs

    #iterate through all samples
    for i in range(len(aYear)):
        aConstructionCost[i] = rateE_kW*np.dot(aPercentSources[i,:]/100, const_costs)
    
    return aConstructionCost

def get_aConsumerCost(aYear, aPercentSources, gen_costs=gen_costs, non_gen_costs=non_gen_costs):
    '''returns an array for the annual consumer cost based on years, percent sources, and generation/non-generation costs for each source'''
    #initalize
    aConsumerCost = np.zeros(len(aYear))
    #interate
    for i in range(len(aYear)):
        P = aPercentSources[i,:]
        aConsumerCost[i] = 0.56*np.dot(gen_costs, P) + 0.44*np.dot(non_gen_costs, P)
    
    return aConsumerCost

def get_aEmissions(aYear, aPercentSources, aEnergy, source_emissions=source_emissions):
    '''returns an array for the total CO2 emissions based on years, percent sources, energy production, and emission data for each source'''
    aEmissions = np.zeros(len(aYear))
    for i in range(len(aYear)):
        P = aPercentSources[i,:]
        aEmissions[i] = aEnergy[i]*np.dot(source_emissions, P)
    
    return aEmissions


def get_totalEmissions(aYear, aEmissions):
    '''returns the net emissions from the arrays for annual emissions and the time in years'''
    delta_t = aYear[-1] - aYear[0]
    n = len(aYear)
    net_em = np.sum(aEmissions)*(delta_t/n)
    return net_em

#### Test of Module ####

if __name__ == "__main__":
    #calculations
    #trying different initial conditions
    sec_der_sources = np.array([-0.5, 0, 1, -0.001, -1, 0.1])

    Years = get_aYear(2021, 2030)
    PercSources = get_aPercentSources(Years, sec_derivative_sources=sec_der_sources)
    
    Energy = get_aEnergy(Years)
    Emissions = get_aEmissions(Years, PercSources, Energy)
    Rel = get_aReliability(Years, PercSources, Energy)
    ConstCost = get_aConstructionCost(Years, PercSources)
    ConsmCost = get_aConsumerCost(Years, PercSources)

    #PLOTS will have 6 figures
    #Fig 1 -- Energy
    #Fig 2 -- CO2
    #Fig 3 -- % Production
    #Fig 4 -- Reliability
    #Fig 5 -- Construction Cost
    #Fig 6 -- Consumer Cost
    
    #plot energy
    plt.figure(0)
    plt.plot(Years, Energy)
    plt.xlabel("Years")
    plt.ylabel("Energy Production MWhr")
    plt.title("Annual Energy Production")
    
    #plot CO2
    plt.figure(1)
    plt.plot(Years, Emissions)
    plt.xlabel("Years")
    plt.ylabel("CO2 Emissions (Million Metric Tons)")
    plt.title("Annual Carbon Emissions")
    print("Total Emissions: ", get_totalEmissions(Years, Emissions))

    #plot the percentages
    plt.figure(2)
    PercCoal = PercSources[:,0]
    PercNG = PercSources[:,1]
    PercSolar = PercSources[:,2]
    PercWind = PercSources[:,3]
    PercNuclear = PercSources[:,4]
    PercWinterNG = PercSources[:,5]

    plt.plot(Years, PercCoal, "k", Years, PercNG, "r", Years, PercSolar, "y", Years, PercWind, "b", Years, PercNuclear, "g", Years, PercWinterNG, "m")
    plt.xlabel("Years")
    plt.ylabel("% Source By Energy Production")
    plt.title("Percent Distribution of Sources Over Time")
    plt.legend(["Coal", "NG", "Solar", "Wind", "Nuclear", "Winterized NG"])

    #plot reliability
    plt.figure(3)
    plt.plot(Years, Rel)
    plt.xlabel("Years")
    plt.ylabel("Reliability (expected reduction in MWh)")
    plt.title("Reliability Over Time")

    
    #plot consutrction cost
    plt.figure(4)
    plt.plot(Years, ConstCost)
    plt.xlabel("Years")
    plt.ylabel("Cost (USD)")
    plt.title("Annual Construction Costs")


    #plot consumer cost
    plt.figure(5)
    plt.plot(Years, ConsmCost)
    plt.xlabel("Years")
    plt.ylabel("Cost (cents/kWh)")
    plt.title("Annual Consumer Costs")
    
    plt.show()