# adopt hyperopt's function to change figsize

import numpy as np
from hyperopt import base
from hyperopt.base import miscs_to_idxs_vals

def plot_hyperopt_vars(
    trials,
    do_show=True,
    fontsize=10,
    colorize_best=None,
    columns=5,
    arrange_by_loss=False,
    figsize=(20,20)
):
    # -- import here because file-level import is too early
    import matplotlib.pyplot as plt

    idxs, vals = miscs_to_idxs_vals(trials.miscs)
    losses = trials.losses()
    finite_losses = [y for y in losses if y not in (None, float("inf"))]
    asrt = np.argsort(finite_losses)
    if colorize_best is not None:
        colorize_thresh = finite_losses[asrt[colorize_best + 1]]
    else:
        # -- set to lower than best (disabled)
        colorize_thresh = finite_losses[asrt[0]] - 1

    loss_min = min(finite_losses)
    loss_max = max(finite_losses)
    print("finite loss range", loss_min, loss_max, colorize_thresh)

    loss_by_tid = dict(zip(trials.tids, losses))

    def color_fn(lossval):
        if lossval is None:
            return 1, 1, 1
        else:
            t = 4 * (lossval - loss_min) / (loss_max - loss_min + 0.0001)
            if t < 1:
                return t, 0, 0
            if t < 2:
                return 2 - t, t - 1, 0
            if t < 3:
                return 0, 3 - t, t - 2
            return 0, 0, 4 - t

    def color_fn_bw(lossval):
        if lossval in (None, float("inf")):
            return 1, 1, 1
        else:
            t = (lossval - loss_min) / (loss_max - loss_min + 0.0001)
            if lossval < colorize_thresh:
                return 0.0, 1.0 - t, 0.0  # -- red best black worst
            else:
                return t, t, t  # -- white=worst, black=best

    all_labels = list(idxs.keys())
    titles = all_labels
    order = np.argsort(titles)

    C = min(columns, len(all_labels))
    R = int(np.ceil(len(all_labels) / float(C)))

    plt.figure(figsize=figsize)
    for plotnum, varnum in enumerate(order):
        label = all_labels[varnum]
        plt.subplot(R, C, plotnum + 1)

        # hide x ticks
        ticks_num, ticks_txt = plt.xticks()
        plt.xticks(ticks_num, [""] * len(ticks_num))

        dist_name = label

        if arrange_by_loss:
            x = [loss_by_tid[ii] for ii in idxs[label]]
        else:
            x = idxs[label]
        if "log" in dist_name:
            y = np.log(vals[label])
        else:
            y = vals[label]
        plt.title(titles[varnum], fontsize=fontsize)
        c = list(map(color_fn_bw, [loss_by_tid[ii] for ii in idxs[label]]))
        if len(y):
            plt.scatter(x, y, c=c)
        if "log" in dist_name:
            nums, texts = plt.yticks()
            plt.yticks(nums, ["%.2e" % np.exp(t) for t in nums])

    if do_show:
        plt.show()