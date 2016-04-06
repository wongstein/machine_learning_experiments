import matplotlib.pyplot as plt



'''
plot scatter plot
'''
class graph():
    my_plot = plt
    def __init__(self, title = None, x_label = None, y_label = None):
        if title:
            self.my_plot.title(title)
        else:
            self.my_plot.title("No Title")
        if x_label:
            self.my_plot.xlabel(x_label, fontsize = 18)
        else:
            self.my_plot.xlabel("X", fontsize = 18)
        if y_label:
            self.my_plot.ylabel(y_label, fontsize = 16)
        else:
            self.my_plot.ylabel("Y", fontsize = 16)

    def plot_scatter_plot(self, x, y, character = None):
        if character in ['o', '^', '.', '<', '>', '1', '2', '3', ',']:
            self.my_plot.plot(x, y, character)
        else:
            self.my_plot.plot(x, y, "o")

    def show_plot(self):
        self.my_plot.show()

