const data = window.VECTOR_DATA;

const width = 900;
const height = 550;
const margin = 50;

const svg = d3.select("#chart")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

const x = d3.scaleLinear()
    .domain(d3.extent(data, d => d.x))
    .nice()
    .range([margin, width - margin]);

const y = d3.scaleLinear()
    .domain(d3.extent(data, d => d.y))
    .nice()
    .range([height - margin, margin]);

const tooltip = d3.select("#tooltip");

svg.selectAll("circle")
    .data(data)
    .enter()
    .append("circle")
    .attr("cx", d => x(d.x))
    .attr("cy", d => y(d.y))
    .attr("r", d => d.type === "query" ? 9 : 6)
    .attr("fill", d => d.type === "query" ? "red" : "steelblue")
    .attr("opacity", 0.8)
    .on("mouseover", function(event, d) {
        d3.select(this).attr("r", 11);

        tooltip
            .style("display", "block")
            .html(`<b>${d.label}</b><br><br>${d.text}`);
    })
    .on("mousemove", function(event) {
        tooltip
            .style("left", `${event.pageX + 10}px`)
            .style("top", `${event.pageY - 20}px`);
    })
    .on("mouseout", function(event, d) {
        d3.select(this).attr("r", d.type === "query" ? 9 : 6);
        tooltip.style("display", "none");
    });

svg.append("text")
    .attr("x", width / 2)
    .attr("y", 25)
    .attr("text-anchor", "middle")
    .style("font-size", "18px")
    .text("Vector Space Visualization");