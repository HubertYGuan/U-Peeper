<script lang="ts">
    import "$lib/U-Peeper_WS"
	import type { WebSocket } from "http";

    let {socket, cmd}: {socket: WebSocket, cmd: 0 | 1 | 2 | 3} = $props();

    let cmd_name = $state("ERROR");
    
    switch (cmd) {
        case CMD_Types.FORWARD:
            cmd_name = "Forward";
            break;
        case CMD_Types.LEFT:
            cmd_name = "Left";
            break;
        case CMD_Types.RIGHT:
            cmd_name = "Right";
            break;
        case CMD_Types.BACK:
            cmd_name = "Back";
            break;
        default:
            break;
    }

    function onclick()
    {
        const arr = new Uint8Array(1);
        arr[0] = cmd;
        socket.send(arr);
    }
</script>

<button {onclick}>
    {cmd_name}
</button>