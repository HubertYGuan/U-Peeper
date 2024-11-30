<script lang="ts">
    import "./Remote_Button.svelte";
    import "$lib/U-Peeper_WS.ts";
	import RemoteButton from "./Remote_Button.svelte";
    // Replace port 8080 with the port of the backend
    let sock: WebSocket = new WebSocket('ws://localhost:8080/remote/ws/');
    
</script>


<h1>U-Peeper Remote</h1>

<RemoteButton socket={sock} cmd={CMD_Types.FORWARD} />