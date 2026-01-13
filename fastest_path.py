import heapq # For priority queue implementation

def dijkstra(graph, origin, destination, weight_key):
    pq = [(0, origin, [origin])]
    visited = set()

    while pq:
        cost, node, path = heapq.heappop(pq) 

        if node == destination: # Found the shortest path to destination
            return cost, path

        if node in visited: # Already visited
            continue
        visited.add(node)

        for neighbor, weights in graph.get(node, {}).items(): # Explore neighbors
            heapq.heappush(
                pq,
                (cost + weights[weight_key], neighbor, path + [neighbor])
            )

    return float("inf"), []


# n8n entry point
input_json = _input.all()[0]["json"] # Get the input JSON

results = []

# Process each shipment
for shipment in input_json["shipments"]: 
    origin = shipment["origin"]
    destination = shipment["destination"]
    priority = shipment.get("priority", "Normal")
    edges = shipment["logisticsNetwork"]["edges"]

    # Build graph
    graph = {}
    for e in edges:
        u, v = e["from"], e["to"]
        graph.setdefault(u, {})[v] = {
            "time": e["timeHours"],
            "cost": e["costEUR"]
        }

    # Priority logic
    priority = priority.lower()

    if priority == "express":
        # Absolute fastest route
        time, path = dijkstra(graph, origin, destination, "time")
        cost, _ = dijkstra(graph, origin, destination, "cost")

    elif priority == "high":
        # Time-first, cost secondary
        time, path = dijkstra(graph, origin, destination, "time")
        cost, _ = dijkstra(graph, origin, destination, "cost")

    elif priority == "medium":
        # Cost-first, time secondary
        cost, path = dijkstra(graph, origin, destination, "cost")
        time, _ = dijkstra(graph, origin, destination, "time")

    else:  # low
        # Cheapest possible route
        cost, path = dijkstra(graph, origin, destination, "cost")
        time, _ = dijkstra(graph, origin, destination, "time")

    # Record results for each batch
    for batch in shipment["batches"]:
        results.append({
            "batchId": batch["batchId"],
            "shipmentId": shipment["shipmentId"],
            "priority": priority,
            "routePlan": {
                "path": path,
                "etaHours": round(time, 2),
                "totalCostEUR": round(cost, 2)
            }
        })

# Output results
return results