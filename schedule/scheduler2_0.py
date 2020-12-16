class Scheduler:
    from pythonds import Graph, Vertex, Stack
    from ra_sched import Schedule, Day
    from datetime import datetime
    import random

    # The scheduler uses a dfs traversal of a graph to
    # generate a ra_sched Schedule according to the
    # following schema:

    # The graph will be comprised of vertices which
    # represent the days of a month that should have
    # a duty shift scheduled. Each vertex is connected
    # by an edge which represents a duty shift.

    # Traversing an edge means assigning a duty shift to
    # a particular RA. Assigning an RA to a duty shift
    # will be determined based on a cost calculated
    # at the time of traversal. This is done because
    # the cost of choosing a particular RA will change
    # for each day.

    def __init__(self):
        self.graph = Graph()
        self.raInfo = {}


    def __setupGraph(self,vertices=[],edges={}):
        # Set up the graph from the provided
        #  vertices and edges. Vertices are Day
        #  objects and edges are a dictionary
        #  where the keys are the date and the
        #  value is a list of tuples containing
        #  the connected date and the assigned RA.

        for v in vertices:
            vt = Vertex(v.date)
            vt.setColor(v)
            self.graph.addVertex(vt)

        for e in edges:
            t = edges[e]
            self.graph.addEdge(e,t[0],t[1])



    def calculateCost(self):
        # Calculate the cost of traversing all
        # edges from a particular vertex and order
        # the results from the lowest cost to the
        # highest.

        # The cost of traversing an edge, aka
        # assigning an RA to a duty shift is calculated
        # based on:
        # 1  The number of points the RA would have after
        #     being assigned the current shift and the
        #     distance from the mean point value
        # 2  The proximity to the last time the RA was
        #     assigned duty
        # 3  The number of times the RA was already
        #     assigned duty for a similar day of the
        #     week (weekdays vs weekends)
        # 4  The number of times the RA was already
        #     assigned for duty in the current month
        # 5  The number of times the RA was assigned for
        #     duty in the previous month
        pass

    def createSchedule(self):
        stateStack = Stack()

if __name__ == "__main__":
    pass
