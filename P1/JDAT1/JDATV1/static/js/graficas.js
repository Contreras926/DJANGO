function crearGraficaVentas(ventasPorProducto) {

    //Ventas Por Producto (BARRAS)
    const canvas = document.getElementById('ventasChart');
    if (!canvas) return;

    const valores = Object.values(ventasPorProducto);

    const colores = valores.map(() => {
        const r = Math.floor(Math.random() * 255);
        const g = Math.floor(Math.random() * 255);
        const b = Math.floor(Math.random() * 255);
        return `rgba(${r}, ${g}, ${b}, 0.7)`;
    }
    );

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: Object.keys(ventasPorProducto),
            datasets: [{
                label: 'Unidades Vendidas',
                data: Object.values(ventasPorProducto),
                backgroundColor: colores,
                borderColor: colores.map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: { display: true, text: 'Ventas por Producto' }
            }
        }
    });
}

function crearGraficaStock(StockData) {
    const canvas = document.getElementById('stockChart');
    if (!canvas) return;

    new Chart(canvas, {
        type: 'pie',
        data: {
            labels: Object.keys(StockData),
            datasets: [{
                label: 'Stock Actual',
                data: Object.values(StockData),
                backgroundColor: [
                    '#FF6384', 
                    '#36A2EB', 
                    '#FFCE56',
                    '#4BC0C0', 
                    '#9966FF', 
                    '#FF9F40'
                ]
            }]
        },
        options: { 
            responsive: true,
        }
    });
}
function cargarGraficas(ventasPorProducto, StockData) {
    crearGraficaVentas(ventasPorProducto);
    crearGraficaStock(StockData);
}