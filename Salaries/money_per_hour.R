library(tidyverse)

dataset <- read.csv("salaries.csv", header=T)

hist(dataset$hourly.wage)
summary(dataset$hourly.wage)

plot(dataset$salary ~ dataset$minutes.played)