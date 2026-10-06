document.addEventListener('input', function (event) {
    if (event.target.type === 'range' || event.target.type === 'number') {
        const rangeId = event.target.id.replace('_input', '');
        const spanId = rangeId + '_value';
        document.getElementById(spanId).textContent = event.target.value;
        flashLabel(rangeId);
    }
});

function flashLabel(id) {
    const label = document.getElementById('label_' + id);
    label.style.backgroundColor = 'yellow';
    setTimeout(() => {
        label.style.backgroundColor = '';
    }, 500);
}

// Add function for showing tooltip on click
function showTooltip(id) {
    const tooltipId = 'tooltip_' + id;
    let tooltip = document.getElementById(tooltipId);

    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = tooltipId;
        tooltip.classList.add('flash-message');
        document.getElementById(id).parentNode.appendChild(tooltip);
    }

    switch(id) {
        case 'system_complexity':
            tooltip.textContent = `Reduced Complexity Information: Accumulated from Domain Mapping Matrix.`;
            break;
        case 'impact':
            tooltip.textContent = `Impact: Accumulated adversarial impact.`;
            break;
        case 'base_score':
            tooltip.textContent = `Base Score: Accumulated adversarial base score.`;
            break;
        case 'exploitability':
            tooltip.textContent = `Exploitability: Accumulated exploitability score.`;
            break;
    }

    tooltip.style.display = 'block';
    setTimeout(() => {
        tooltip.style.display = 'none';
    }, 5000); // Auto-hide after 5 seconds
}

function hideTooltip(id) {
    const tooltipId = 'tooltip_' + id;
    const tooltip = document.getElementById(tooltipId);
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

// Trapezoidal membership function for fuzzy logic
function trapezoidalMembership(x, a, b, c, d) {
    if (x <= a || x >= d) return 0;
    else if (x >= b && x <= c) return 1;
    else if (x > a && x < b) return (x - a) / (b - a);
    else return (d - x) / (d - c);
}

function syncInput(id) {
    const range = document.getElementById(id);
    const input = document.getElementById(id + '_input');
    input.value = range.value;
    document.getElementById(id + '_value').textContent = range.value;
    flashLabel(id);
}

function syncRange(id) {
    const range = document.getElementById(id);
    const input = document.getElementById(id + '_input');
    range.value = input.value;
    document.getElementById(id + '_value').textContent = input.value;
    flashLabel(id);
}

function computeRisk() {
    const system_complexity = parseFloat(document.getElementById('system_complexity').value);
    const impact = parseFloat(document.getElementById('impact').value);
    const base_score = parseFloat(document.getElementById('base_score').value);
    const exploitability = parseFloat(document.getElementById('exploitability').value);

    // Membership functions for reduced complexity information
    const systemComplexityLow = trapezoidalMembership(system_complexity, 1, 1, 8, 15);
    const systemComplexityMedium = trapezoidalMembership(system_complexity, 10, 15, 18, 25);
    const systemComplexityHigh = trapezoidalMembership(system_complexity, 20, 25, 45, 55);
    const systemComplexityVeryHigh = trapezoidalMembership(system_complexity, 50, 55, 100, 100);

    // Membership functions for impact
    const impactLow = trapezoidalMembership(impact, 0, 0, 2.5, 2.5);
    const impactMedium = trapezoidalMembership(impact, 3, 4, 6, 7);
    const impactHigh = trapezoidalMembership(impact, 6.5, 7.5, 8.5, 9.5);
    const impactCritical = trapezoidalMembership(impact, 9, 9.5, 10, 10);

    // Membership functions for base score
    const baseScoreLow = trapezoidalMembership(base_score, 0, 0, 2.5, 2.5);
    const baseScoreMedium = trapezoidalMembership(base_score, 3, 4, 6, 7);
    const baseScoreHigh = trapezoidalMembership(base_score, 6.5, 7.5, 8.5, 9.5);
    const baseScoreCritical = trapezoidalMembership(base_score, 9, 9.5, 10, 10);

    // Membership functions for exploitability
    const exploitabilityLow = trapezoidalMembership(exploitability, 0, 0, 2.5, 2.5);
    const exploitabilityMedium = trapezoidalMembership(exploitability, 3, 4, 6, 7);
    const exploitabilityHigh = trapezoidalMembership(exploitability, 6.5, 7.5, 8.5, 9.5);
    const exploitabilityCritical = trapezoidalMembership(exploitability, 9, 9.5, 10, 10);

    // Apply fuzzy rules (including additional rules)
    const rule1 = Math.min(systemComplexityLow, impactLow, baseScoreLow, exploitabilityLow);
    const rule2 = Math.min(systemComplexityMedium, impactMedium, baseScoreMedium, exploitabilityMedium);
    const rule3 = Math.min(systemComplexityHigh, impactHigh, baseScoreHigh, exploitabilityHigh);
    const rule4 = Math.min(systemComplexityVeryHigh, impactCritical, baseScoreCritical, exploitabilityCritical);
    const rule5 = Math.min(systemComplexityHigh, impactMedium, baseScoreLow, exploitabilityHigh);
    const rule6 = Math.min(systemComplexityHigh, impactMedium, baseScoreLow, exploitabilityMedium);
    const rule7 = Math.min(systemComplexityMedium, impactCritical, baseScoreMedium, exploitabilityMedium);
    const rule8 = Math.min(systemComplexityLow, impactHigh, baseScoreLow, exploitabilityHigh);
    const rule9 = Math.min(systemComplexityHigh, impactMedium, baseScoreMedium, exploitabilityLow); // New Rule
    const rule10 = Math.min(systemComplexityHigh, impactMedium, baseScoreHigh, exploitabilityLow); // High Complexity, Medium Impact, High Base Score, Low Exploitability
    const rule11 = Math.min(systemComplexityVeryHigh, impactHigh, baseScoreHigh, exploitabilityMedium); // Very High Complexity, High Impact, High Base Score, Medium Exploitability

    // Aggregating risk values (Defuzzification using weighted average)
    const riskValue = (rule1 * 20 + rule2 * 55 + rule3 * 80 + rule4 * 100 + rule5 * 80 + rule6 * 55 +
                       rule7 * 75 + rule8 * 30 + rule9 * 55 + rule10 * 74 + rule11 * 85) /
                      (rule1 + rule2 + rule3 + rule4 + rule5 + rule6 + rule7 + rule8 + rule9 + rule10 + rule11);

     // Determine the risk level
     let riskLevel = '';
     if (riskValue >= 90) {
         riskLevel = 'Catastrophic Risk';
     } else if (riskValue >= 70) {
         riskLevel = 'High Risk';
     } else if (riskValue >= 40) {
         riskLevel = 'Medium Risk';
     } else {
         riskLevel = 'Low Risk';
     }

     document.getElementById("risk_value").textContent = isNaN(riskValue) ? '-' : riskValue.toFixed(2);
     document.getElementById("risk_level").textContent = isNaN(riskValue) ? '-' : riskLevel;

     // Update chart
     updateRiskChart(riskValue);
 }




// Chart.js configuration
const ctx = document.getElementById('riskChart').getContext('2d');

// Data for trapezoidal membership functions
const riskLabels = [0, 20, 30, 40, 50, 60, 70, 80, 90, 100];

// Membership data for each risk level (trapezoidal shape)
const lowRiskData = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0];         // Low risk (1 at 0, 0 at 40)
const mediumRiskData = [0, 0, 0, 1, 1, 1, 0, 0, 0, 0];      // Medium risk (1 peak at 40, descent starts at 60)
const highRiskData = [0, 0, 0, 0, 0, 0, 1, 1, 0, 0];        // High risk (1 peak at 70, decline starts at 80)
const catastrophicRiskData = [0, 0, 0,, 0, 0, 0, 0, 1, 1, 1]; // Catastrophic risk (1 peak at 90, no descent)

const riskChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: riskLabels,
        datasets: [{
            label: 'Low Risk',
            data: lowRiskData,
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderWidth: 2,
            fill: true, // Fill the area under the line
        },
        {
            label: 'Medium Risk',
            data: mediumRiskData,
            borderColor: 'rgba(255, 206, 86, 1)',
            backgroundColor: 'rgba(255, 206, 86, 0.2)',
            borderWidth: 2,
            fill: true, // Fill the area under the line
        },
        {
            label: 'High Risk',
            data: highRiskData,
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 2,
            fill: true, // Fill the area under the line
        },
        {
            label: 'Catastrophic Risk',
            data: catastrophicRiskData,
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderWidth: 2,
            fill: true, // Fill the area under the line
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                max: 1,
                title: {
                    display: true,
                    text: 'Membership',
                    font: {
                        size: 16
                    }
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Risk',
                    font: {
                        size: 16
                    }
                },
                ticks: {
                    min: 0,
                    max: 100,
                    stepSize: 10
                }
            }
        }
    }
});

function updateRiskChart(riskValue) {
    if (riskValue !== null) {
        const data = [0, 0, 0, 0]; // Reset the highlight on all risk levels

        if (riskValue <= 39) data[0] = riskValue; // Low risk
        else if (riskValue <= 69) data[1] = riskValue; // Medium risk
        else if (riskValue <= 89) data[2] = riskValue; // High risk
        else data[3] = riskValue; // Catastrophic risk

        // Adjust opacity for the active risk level
        riskChart.data.datasets[0].backgroundColor = riskValue <= 39 ? 'rgba(54, 162, 235, 0.6)' : 'rgba(54, 162, 235, 0.2)';
        riskChart.data.datasets[1].backgroundColor = riskValue > 39 && riskValue <= 69 ? 'rgba(255, 206, 86, 0.6)' : 'rgba(255, 206, 86, 0.2)';
        riskChart.data.datasets[2].backgroundColor = riskValue > 69 && riskValue <= 89 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(75, 192, 192, 0.2)';
        riskChart.data.datasets[3].backgroundColor = riskValue > 89 ? 'rgba(255, 99, 132, 0.6)' : 'rgba(255, 99, 132, 0.2)';

        riskChart.update(); // Refresh the chart
    }
}

// Reset button logic to reset the sliders and inputs to default
document.getElementById('resetButton').addEventListener('click', function () {
    document.getElementById('system_complexity').value = 0;
    document.getElementById('impact').value = 0;
    document.getElementById('base_score').value = 0;
    document.getElementById('exploitability').value = 0;
    syncInput('system_complexity');
    syncInput('impact');
    syncInput('base_score');
    syncInput('exploitability');
    updateRiskChart(0); // Reset the chart
    document.getElementById("risk_value").textContent = '-';
    document.getElementById("risk_level").textContent = '-';
});
