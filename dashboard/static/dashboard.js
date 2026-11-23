
const statusNames = {
    available: "Disponível",
    occupied: "Ocupada",
    unknown: "Sem dados válidos"
};

const roomNames = {
    room_A: "Sala 01",
    room_B: "Sala 02",
    room_C: "Sala 03"
};

function measurement(value, unit) {
    return value == null ? "—" : `${value} ${unit}`;
}

async function updateDashboard() {
    const connection = document.getElementById("connection");

    try {
        // Consulta os dados da API
        const [roomsResponse, metricsResponse] = await Promise.all([
            fetch("/api/rooms", { cache: "no-store" }),
            fetch("/api/metrics", { cache: "no-store" })
        ]);

        if (!roomsResponse.ok || !metricsResponse.ok) {
            throw new Error("Falha ao consultar a API");
        }

        const rooms = await roomsResponse.json();
        const metrics = await metricsResponse.json();

        // Atualiza os indicadores
        document.getElementById("available").textContent =
            metrics.available_rooms;

        document.getElementById("occupied").textContent =
            metrics.occupied_rooms;

        document.getElementById("unknown").textContent =
            metrics.rooms_without_current_data;

        const container = document.getElementById("rooms");
        container.replaceChildren();

        // Cria os cartões das salas
        for (const room of rooms) {
            const card = document.createElement("article");

            const statusValue = room.connected
                ? room.status
                : "unknown";

            card.className = `room ${statusValue}`;

            const title = document.createElement("h3");
            title.textContent = roomNames[room.room] ?? room.room;

            const status = document.createElement("strong");
            status.textContent = statusNames[statusValue] ?? "Desconhecido";

            const details = document.createElement("p");

            details.textContent =
                `Pessoas: ${room.connected ? room.occupancy : "—"} | ` +
                `Temperatura: ${measurement(room.temperature, "°C")}`;

            card.append(title, status, details);
            container.appendChild(card);
        }

        connection.textContent =
            `Última atualização: ${new Date().toLocaleTimeString("pt-BR")}`;

    } catch (error) {
        connection.textContent = "Não foi possível atualizar os dados.";
        console.error("Erro ao atualizar o SmartSpace:", error);
    }
}

// Atualiza a cada 5 segundos
updateDashboard();
setInterval(updateDashboard, 5000);
