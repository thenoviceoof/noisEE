library(segmented)
library(ggplot2)

data = read.csv(file="gains_20k_60_nonlinear.csv", head=TRUE, sep=",")

breakpoints = function(x, y, number) {
    initialBreakpoints = seq(-20, 0, length.out=number+2)[2:(number + 1)]
    segments = segmented(lm(y~x), seg.Z = ~x, psi=initialBreakpoints)
    segments
}

plotBreakpoints = function(x, y, number, name) {
    breakpointData = breakpoints(x, y, number)
    dataFrame = data.frame(x = x,
                           y = y,
                           yLinear = broken.line(breakpointData)$fit)
    (plot = ggplot(dataFrame, aes(x=x, y=y), color='red')
        + geom_line()
        + geom_line(aes(x=x, y=yLinear), color='blue')
    )
    ggsave(filename=paste("linear_plot_", name, ".png", sep=""), plot)
    breakpointData
}

# Sometimes the segmented fit will randomly fail, so keep the
# randomness fixed on a working value.
set.seed(3)

cModel = plotBreakpoints(data[, 1], data[, 3], 6, "constant")
lModel = plotBreakpoints(data[, 1], data[, 2], 6, "low")
mModel = plotBreakpoints(data[, 1], data[, 4], 6, "med")
hModel = plotBreakpoints(data[, 1], data[, 5], 6, "high")

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
