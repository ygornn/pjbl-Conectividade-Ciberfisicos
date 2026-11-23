
const statusNames = {
    available: "Disponível",
    occupied: "Ocupada",
    unknown: "Sem dados válidos"
};

function measurement(value, unit) {
    return value == null ? "—" : `${value} ${unit}`;
}

async function updateDashboard() {
    const connection = document.getElementById("connection");

    try {
        const [roomsResponse, metricsResponse] = await Promise.all([
            fetch("/api/rooms"),
            fetch("/api/metrics")
        ]);

        if (!roomsResponse.ok || !metricsResponse.ok) {
            throw new Error("Falha ao consultar a API");
        }

        const rooms = await roomsResponse.json();
        const metrics = await metricsResponse.json();

        document.getElementById("available").textContent =
            metrics.available_rooms;

        document.getElementById("occupied").textContent =
            metrics.occupied_rooms;

        document.getElementById("unknown").textContent =
            metrics.rooms_without_current_data;

        const container = document.getElementById("rooms");
        container.replaceChildren();

        for (const room of rooms) {
            const card = document.createElement("article");
            card.className = `room ${room.status}`;

            const title = document.createElement("h3");
            title.textContent = room.name;

            const status = document.createElement("strong");
            status.textContent = statusNames[room.status] ?? "Desconhecido";

            const details = document.createElement("p");
            details.textContent =
                `Pessoas: ${room.connected ? room.occupancy : "—"} | ` +
                `Temperatura: ${measurement(room.temperature, "°C")} | ` +
                `Umidade: ${measurement(room.humidity, "%")} | ` +
                `Ruído: ${measurement(room.noise_db, "dB")}`;

            card.append(title, status, details);
            container.appendChild(card);
        }

        connection.textContent = "Consulta à API realizada com sucesso.";

    } catch (error) {
        connection.textContent = "Não foi possível atualizar os dados.";
        console.error(error);
    }
}

updateDashboard();
setInterval(updateDashboard, 5000);
