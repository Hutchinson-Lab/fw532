# effect_plot.R -- marginal and partial effect plots for fitted models (FW 532)
#
# Used by r/demo-effect-plots.qmd:  source(here::here("r", "effect_plot.R"))
#
# effect_plot()     computes (and, for one variable, plots) the marginal and/or
#                   partial effect of one or two predictors on a model's predictions.
# plot_effect_2D()  draws a two-variable result from effect_plot() as an
#                   interactive plotly surface.

library(ggplot2)
library(plotly)

effect_plot <- function(
    model,
    data,
    vars,
    effect_type = c("marginal", "partial", "both"),
    grid = c("unique", "range", "observed"),
    granularity = 200,
    type = NULL,
    plot = TRUE,
    rug = TRUE,       # Default: TRUE for 1D and 2D
    truth = NULL,     # optional data.frame(var, pred, type) of true effects, drawn dashed (1D only)
    title = NULL,     # optional plot title (1D only)
    ...
) {
  effect_type <- match.arg(effect_type)
  grid <- match.arg(grid)

  if (!all(vars %in% names(data))) stop("Some vars not in data")

  make_grid <- function(v) {
    if (grid=="range") seq(min(data[[v]], na.rm=TRUE), max(data[[v]], na.rm=TRUE), length.out=granularity)
    else if (grid=="observed") data[[v]]
    else sort(unique(data[[v]]))
  }

  # the "typical" value used for the other variables in a marginal effect:
  # the mean of a numeric column (for a factor column, its first value)
  typical_value <- function(x) {
    if (is.numeric(x)) mean(x, na.rm=TRUE) else x[1]
  }

  pred_fun <- function(mod, newdata, type, ...) {

    # ---- randomForest support ----
    if (inherits(mod, "randomForest")) {

      # Classification
      if (!is.null(mod$classes)) {

        # Probability prediction
        if (!is.null(type) && type == "prob") {
          probs <- predict(mod, newdata = newdata, type = "prob", ...)

          # If binary: return probability of class 2 (positive class)
          if (ncol(probs) == 2) {
            return(probs[, 2])
          }

          # If multiclass: return probability of predicted class
          return(apply(probs, 1, max))
        }

        # Class prediction -> convert to numeric for consistency
        preds <- predict(mod, newdata = newdata, type = "response", ...)
        return(as.numeric(preds))
      }

      # Regression
      return(predict(mod, newdata = newdata, ...))
    }

    # ---- GBM ----
    if ("gbm" %in% class(mod) && !is.null(type)) {
      return(predict(mod, newdata = newdata, type = type, ...))
    }

    # ---- default ----
    if (!is.null(type)) {
      return(
        tryCatch(
          predict(mod, newdata = newdata, type = type, ...),
          error = function(e) predict(mod, newdata = newdata, ...)
        )
      )
    }

    predict(mod, newdata = newdata, ...)
  }


  # -------------------- 1D --------------------
  if (length(vars)==1) {
    var <- vars[1]
    x_vals <- make_grid(var)

    compute_1d <- function(effect_kind) {
      if (effect_kind=="marginal") {
        # every other variable at its typical value; only `var` changes
        nd <- as.data.frame(lapply(data, function(x) rep(typical_value(x), length(x_vals))))
        nd[[var]] <- x_vals
        preds <- pred_fun(model, nd, type, ...)
      } else if (effect_kind=="partial") {
        # for each grid value: set `var` to that value for EVERY row of the data,
        # keep the other variables as observed, predict, and average
        preds <- numeric(length(x_vals))
        for (i in seq_along(x_vals)) {
          nd <- data; nd[[var]] <- x_vals[i]
          preds[i] <- mean(pred_fun(model, nd, type, ...))
        }
      }
      data.frame(var=x_vals, pred=as.vector(preds), type=effect_kind)
    }

    if (effect_type=="both") {
      df <- rbind(compute_1d("marginal"), compute_1d("partial"))
    } else {
      df <- compute_1d(effect_type)
    }

    if (plot) {
      if (is.null(title)) {
        title <- paste(ifelse(effect_type=="both","Marginal vs Partial", toupper(effect_type)), "Effect of", var)
      }
      p <- ggplot(df, aes(x=var, y=pred, color=type)) +
        geom_line(aes(linetype="fitted model"), linewidth=1.2) +
        labs(
          x = var,
          y = "Predicted Response",
          title = title,
          color = "Effect Type",
          linetype = NULL
        ) +
        theme_minimal() +
        ylim(0,1)

      if (!is.null(truth)) {
        p <- p + geom_line(data=truth, aes(linetype="truth"), linewidth=0.8)
      }
      p <- p + scale_linetype_manual(values=c("fitted model"="solid", "truth"="dashed"))

      if (rug) {
        p <- p + geom_rug(data=data, aes(x=.data[[var]]), inherit.aes=FALSE,
                          sides="b", alpha=0.3, color="black")
      }

      print(p)
    }

    return(df)
  }

  # -------------------- 2D --------------------
  if (length(vars)==2) {
    var1 <- vars[1]; var2 <- vars[2]
    x1 <- make_grid(var1); x2 <- make_grid(var2)
    grid_df <- expand.grid(var1=x1, var2=x2)

    if (effect_type=="marginal") {
      base <- as.data.frame(lapply(data, typical_value))
      nd <- base[rep(1, nrow(grid_df)), ]
      nd[[var1]] <- grid_df$var1; nd[[var2]] <- grid_df$var2
      preds <- pred_fun(model, nd, type, ...)
      df <- cbind(grid_df, pred=as.vector(preds))
    } else if (effect_type=="partial") {
      pd_vals <- numeric(nrow(grid_df))
      for (i in seq_len(nrow(grid_df))) {
        nd <- data; nd[[var1]] <- grid_df$var1[i]; nd[[var2]] <- grid_df$var2[i]
        pd_vals[i] <- mean(pred_fun(model, nd, type, ...))
      }
      df <- cbind(grid_df, pred=pd_vals)
    } else {
      stop("2D plots currently support only 'marginal' or 'partial'.")
    }

    if (plot) {
      print(plot_effect_2D(df, data_points = if (rug) data[, c(var1, var2)] else NULL,
                           axis_titles = c(var1, var2), rug = rug))
    }

    return(df)
  }

  stop("Specify 1 or 2 variables in vars.")
}



plot_effect_2D <- function(
    df,
    varnames = c("var1","var2"),
    predname = "pred",
    data_points = NULL,        # optional: original data for rug/scatter (first two columns are used)
    axis_titles = varnames,    # axis labels, e.g. the real variable names
    colorscale = "Earth",
    opacity = 0.9,
    point_color = "black",
    point_size = 2,
    rug = TRUE,
    zlim = NULL                # optional c(min, max) for the z axis and colors, e.g. c(0, 1)
) {
  # Prepare surface. expand.grid() varies var1 fastest, so filling a matrix by column
  # gives rows = var1 values and columns = var2 values.
  x_vals <- sort(unique(df[[varnames[1]]]))
  y_vals <- sort(unique(df[[varnames[2]]]))
  z_mat <- matrix(df[[predname]], nrow = length(x_vals), ncol = length(y_vals))

  # plotly expects the rows of z to go with y and the columns with x, hence t()
  p <- plot_ly(
    x = x_vals,
    y = y_vals,
    z = t(z_mat),
    type = "surface",
    colorscale = colorscale,
    opacity = opacity,
    cmin = if (is.null(zlim)) NULL else zlim[1],
    cmax = if (is.null(zlim)) NULL else zlim[2]
  )

  # Add empirical data as scatter on bottom plane
  if (!is.null(data_points) && rug) {
    z_min <- if (is.null(zlim)) min(df[[predname]], na.rm = TRUE) else zlim[1]
    p <- p %>% add_markers(
      x = data_points[[1]],
      y = data_points[[2]],
      z = rep(z_min, nrow(data_points)),
      marker = list(color = point_color, size = point_size),
      inherit = FALSE,
      showlegend = FALSE
    )
  }

  p <- p %>% layout(
    scene = list(
      xaxis = list(title = axis_titles[1]),
      yaxis = list(title = axis_titles[2]),
      zaxis = list(title = "Predicted Response",
                   range = if (is.null(zlim)) NULL else zlim)
    )
  )

  return(p)
}
