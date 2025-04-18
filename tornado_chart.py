import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from highlight_text import ax_text

def tornado_chart(data,labels, midpoint, low_values, high_values, title="<Low> VS <High> values"):
    """
    Parameters
    ----------
    labels : np.array()
        List of label titles used to identify the variables, y-axis of bar
        chart. The lengh of labels is used to itereate through to generate 
        the bar charts.
    midpoint : float
        Center value for bar charts to extend from. In sensitivity analysis
        this is often the 'neutral' or 'default' model output.
    low_values : np.array()
        An np.array of the model output resulting from the low variable 
        selection. Same length and order as label_range. 
    high_values : np.array()
        An np.array of the model output resulting from the high variable
        selection. Same length and order as label_range.
    """
    
    color_low = '#e1ceff'
    color_high = '#ff6262'
    
    ys = range(len(data['Labels']))[::1] # iterate through # of labels
    
    for y, low_value, high_value in zip(ys, low_values, high_values):
    
        low_width = midpoint - low_value
        high_width = high_value - midpoint
    
        plt.broken_barh(
            [
                (low_value, low_width),
                (midpoint, high_width)
            ],
            (y-0.4, 0.8), # thickness of bars and their offset
            facecolors = [color_low, color_high],
            edgecolors = ['black', 'black'],
            linewidth = 0.5
            )
        
        offset = 2 # offset value labels from end of bar
        
        if high_value > low_value:
            x_high = midpoint + high_width + offset 
            x_low = midpoint - low_width - offset
        else:
            x_high = midpoint + high_width - offset
            x_low = midpoint - low_width + offset

        plt.text(x_high, y, str(high_value), va='center', ha='center')
        plt.text(x_low, y, str(low_value), va='center', ha='center')
    
    plt.axvline(midpoint, color='black', linewidth = 1)

    # set axis lines on or off
    ax = plt.gca() 
    ax.spines[['right', 'left', 'top']].set_visible(False)
    ax.set_yticks([])
    
    # build legend 
    ax_text(x = midpoint, y = len(labels),
            s=title,
            color='black',
            fontsize=15,
            va='center',
            ha='center',
            highlight_textprops=[{"color": color_low, "fontweight": 'bold'},
                                 {"color": color_high, "fontweight": 'bold'}],
            ax=ax)
    
    plt.xlabel('Model output')
    plt.yticks(ys, labels)
    plt.xlim(0,40)
    plt.ylim(-0.5, len(labels)-0.5)
    plt.tick_params(left = False)
    plt.show()
    
    return