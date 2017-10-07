################################################################################
## Copyright 2017 "Nathan Hwang" <thenoviceoof>
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
################################################################################

library(segmented)
library(ggplot2)

data = read.csv(file="gains_20k_60_nonlinear.csv", head=TRUE, sep=",")

breakpoints = function(x, y, number) {
    initialBreakpoints = seq(-20, 0, length.out=number+2)[2:(number + 1)]
    segments = segmented(lm(y~x), seg.Z = ~x, psi=initialBreakpoints)
    segments
}

plotBreakpoints = function(x, y, number, name, cutoff) {
    breakpointData = breakpoints(x, y, number)
    dataFrame = data.frame(x = x,
                           y = y,
                           yLinear = broken.line(breakpointData)$fit)
    (plot = ggplot(dataFrame, aes(x=x, y=y))
        + geom_line(color='red')
        + geom_line(aes(x=x, y=yLinear), color='blue')
        + ggtitle(paste(name, " filter gain ", cutoff, sep=""))
        + xlab("Slope (db/decade)")
        + ylab("Gain")
    )
    # Width/height are in inches.
    ggsave(filename=paste("linear_plot_", name, ".png", sep=""), plot, width=3, height=3)
    breakpointData
}

# Sometimes the segmented fit will randomly fail, so keep the
# randomness fixed on a working value.
set.seed(3)

cModel = plotBreakpoints(data[, 1], data[, 3], 6, "constant", "(no filter)")
lModel = plotBreakpoints(data[, 1], data[, 2], 6, "low", "(16.5Hz)")
mModel = plotBreakpoints(data[, 1], data[, 4], 6, "med", "(270Hz)")
hModel = plotBreakpoints(data[, 1], data[, 5], 6, "high", "(5300Hz)")

getBreakpoints = function(model) {
    # Extract the x value of the breakpoints.
    x = c(c(-20.0), model$psi[, 2], c(0.0))
    
    # And get the modeled y-values.
    y = predict(model, data.frame(x = x))
    # Do a little bit of data clean up: prevent negative values.
    y[y < 0] = 0
    data.frame(x = x, y = y)
}

cBreak = getBreakpoints(cModel)
lBreak = getBreakpoints(lModel)
mBreak = getBreakpoints(mModel)
hBreak = getBreakpoints(hModel)

# Package up everything into a csv.
mat = matrix(c(
    c(cBreak$x, cBreak$y),
    c(lBreak$x, lBreak$y),
    c(mBreak$x, mBreak$y),
    c(hBreak$x, hBreak$y)),
    ncol = length(cBreak$x) + length(cBreak$y),
    byrow=TRUE)
rownames(mat) = c("Constant (2.000.000hz)",
                  "Low (16.5hz)",
                  "Medium (270hz)",
                  "High (5300hz)")
colnames(mat) = c(paste("x", lapply(seq(1, 8, by = 1), toString), sep=""),
                  paste("y", lapply(seq(1, 8, by = 1), toString), sep=""))
print(mat)

write.csv(mat, file="linear_parameters.csv", quote=FALSE)
