// --- Dijkstra & Helper Functions ---
const mathInf = Number.POSITIVE_INFINITY;

function buildGraph(edges) {
  const g = {};
  if (!edges) return g;
  for (const e of edges) {
    const from = e["from"];
    const to = e["to"];
    if (!g[from]) g[from] = {};
    g[from][to] = {
      distanceKm: Number(e["distanceKm"]),
      timeHours: Number(e["timeHours"]),
      costEUR: Number(e["costEUR"]),
    };
  }
  return g;
}

class MinHeap {
  constructor() { this.a = []; }
  size() { return this.a.length; }
  push(item) {
    this.a.push(item);
    this._siftUp(this.a.length - 1);
  }
  pop() {
    if (this.a.length === 0) return null;
    const top = this.a[0];
    const last = this.a.pop();
    if (this.a.length > 0) {
      this.a[0] = last;
      this._siftDown(0);
    }
    return top;
  }
  _siftUp(i) {
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (this.a[p][0] <= this.a[i][0]) break;
      [this.a[p], this.a[i]] = [this.a[i], this.a[p]];
      i = p;
    }
  }
  _siftDown(i) {
    const n = this.a.length;
    while (true) {
      let smallest = i;
      const l = 2 * i + 1;
      const r = 2 * i + 2;
      if (l < n && this.a[l][0] < this.a[smallest][0]) smallest = l;
      if (r < n && this.a[r][0] < this.a[smallest][0]) smallest = r;
      if (smallest === i) break;
      [this.a[i], this.a[smallest]] = [this.a[smallest], this.a[i]];
      i = smallest;
    }
  }
}

function dijkstra(graph, origin, destination, weightKey) {
  const pq = new MinHeap();
  pq.push([0.0, origin, [origin]]);
  const visited = new Set();
  while (pq.size() > 0) {
    const [cost, node, path] = pq.pop();
    if (node === destination) return [cost, path];
    if (visited.has(node)) continue;
    visited.add(node);
    const nbrs = graph[node] || {};
    for (const [nxt, w] of Object.entries(nbrs)) {
      pq.push([cost + Number(w[weightKey]), nxt, path.concat([nxt])]);
    }
  }
  return [mathInf, []];
}

function sumAlongPath(graph, path) {
  let dist = 0.0, time = 0.0, cost = 0.0;
  for (let i = 0; i < path.length - 1; i++) {
    const w = graph[path[i]][path[i+1]];
    dist += w.distanceKm;
    time += w.timeHours;
    cost += w.costEUR;
  }
  return [dist, time, cost];
}

// --- Main n8n Logic ---

// Access the merged input item
const input = $input.first().json;

// Extract shipments and network from the merged object
const shipmentsList = input.shipments || [];
// Access edges from the network data part of the merge
const edges = input.edges || []; 
const graph = buildGraph(edges);

const results = shipmentsList.map(sh => {
  const origin = sh.origin;
  const destination = sh.destination;
  const priority = sh.priority;

  const prNorm = ((priority ?? "low") + "").toLowerCase();
  const weightKey = (prNorm === "express" || prNorm === "high") ? "timeHours" : "costEUR";

  const [totalWeight, path] = dijkstra(graph, origin, destination, weightKey);

  // Initialize structure
  let distanceKm = 0, timeHours = 0, costEUR = 0;
  
  if (path && path.length > 1) {
    const totals = sumAlongPath(graph, path);
    distanceKm = Number(totals[0].toFixed(1));
    timeHours = Number(totals[1].toFixed(1));
    costEUR = Number(totals[2].toFixed(1));
  }

  return {
    shipmentId: sh.shipmentId,
    origin,
    destination,
    route: path,
    distanceKm,
    timeHours,
    costEUR,
    priority,
    logisticsNetwork: {
      edges: path.length > 1 ? [{
        from: origin,
        to: destination,
        timeHours,
        costEUR
      }] : []
    },
    batches: sh.batches || []
  };
});

return {
  json: {
    shipments: results
  }
};