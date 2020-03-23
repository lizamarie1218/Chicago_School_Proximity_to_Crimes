import * as d3 from "d3";


chart = {
  const svg = d3.create("svg")
      .attr("viewBox", [0, 0, 975, 610]);

  svg.append("path")
      .datum(topojson.merge(us, us.objects.states.geometries.filter(d => d.id !== "02" && d.id !== "15")))
      .attr("fill", "#ddd")
      .attr("d", d3.geoPath());

  svg.append("path")
      .datum(topojson.mesh(us, us.objects.states, (a, b) => a !== b))
      .attr("fill", "none")
      .attr("stroke", "white")
      .attr("stroke-linejoin", "round")
      .attr("d", d3.geoPath());

  svg.append("g")
      .attr("fill", "none")
      .attr("stroke", "red")
      .attr("pointer-events", "all")
    .selectAll("path")
    .data(d3.geoVoronoi().polygons(data).features)
    .join("path")
      .attr("d", d3.geoPath(projection))
    .append("title")
      .text(d => {
        const p = d.properties.site.properties;
        return `${p.name} Airport
${p.city}, ${p.state}`;
      });

  svg.append("path")
      .datum({type: "FeatureCollection", features: data})
      .attr("d", d3.geoPath(projection).pointRadius(1.5));

  return svg.node();
}

// data = [obj, obj, ... , obj]

data = d3.csvParse(await FileAttachment("airports.csv").text(), d => ({
  type: "Feature",
  properties: d,
  geometry: {
    type: "Point",
    coordinates: [+d.longitude, +d.latitude]
  }
}))

projection = ƒ(t)

projection = d3.geoAlbers().scale(1300).translate([487.5, 305])

us = Object {type: "Topology", bbox: Array(4), transform: Object, objects: Object, arcs: Array(305)}

us = d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-albers-10m.json")

topojson = Object {bbox: ƒ(e), feature: ƒ(e, t), merge: ƒ(e), mergeArcs: ƒ(e, t), mesh: ƒ(e), meshArcs: ƒ(e, t, r), neighbors: ƒ(e), quantize: ƒ(e, t), transform: ƒ(e), untransform: ƒ(e)}

topojson = require("topojson-client@3")

d3 = Object {format: ƒ(t), formatPrefix: ƒ(t, n), timeFormat: ƒ(t), timeParse: ƒ(t), utcFormat: ƒ(t), utcParse: ƒ(t), FormatSpecifier: ƒ(t), active: ƒ(t, n), arc: ƒ(), area: ƒ(), areaRadial: ƒ(), ascending: ƒ(t, n), autoType: ƒ(t), axisBottom: ƒ(t), axisLeft: ƒ(t), axisRight: ƒ(t), axisTop: ƒ(t), bisect: ƒ(n, e, r, i), bisectLeft: ƒ(n, e, r, i), bisectRight: ƒ(n, e, r, i), …}

d3 = require("d3@5", "d3-geo-voronoi@1")