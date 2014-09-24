var client = new Keen({
  projectId: "your_project_id",
  readKey: "your_read_key"
});

Keen.ready(function(){
  var query = new Keen.Query("maximum", {
    eventCollection: "task_counts",
    timeframe: "previous_14_days",
    targetProperty: "closed",
    interval: "daily"
  });
  client.draw(query, document.getElementById("burnup_chart"), {
    // Custom configuration here
  });
});
