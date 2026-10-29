document.addEventListener("DOMContentLoaded", function () {

  // Basic browser-side form validation
  const form = document.getElementById("registration-form");
  if (form) {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        form.reportValidity();
      }
    });
  }

  // Read chart information safely from the HTML
  function getChartData(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
      return {};
    }
    try {
      return JSON.parse(element.textContent);
    } catch (error) {
      console.error("Could not read chart data:", error);
      return {};
    }
  }

  // Display charts only when Chart.js is available
  if (typeof Chart !== "undefined") {
    const sourceData = getChartData("source-data");
    const referralData = getChartData("referral-data");

    const sourceCanvas = document.getElementById("sourceChart");
    if (sourceCanvas) {
      new Chart(sourceCanvas, {
        type: "doughnut",
        data: {
          labels: Object.keys(sourceData),
          datasets: [{
            label: "Registrations",
            data: Object.values(sourceData)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      });
    }

    const referralCanvas = document.getElementById("referralChart");
    if (referralCanvas) {
      new Chart(referralCanvas, {
        type: "bar",
        data: {
          labels: Object.keys(referralData),
          datasets: [{
            label: "Registrations",
            data: Object.values(referralData),
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0
              }
            }
          }
        }
      });
    }
  }
});