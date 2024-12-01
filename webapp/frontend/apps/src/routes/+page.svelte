<script lang="ts">
	import './Remote_Button.svelte';
	import '$lib/U-Peeper_WS.ts';
	import RemoteButton from './Remote_Button.svelte';
	import { WebSocket as WS } from 'ws';
    import type { MessageEvent } from 'ws';
	import { CMD_Types } from '$lib/U-Peeper_WS.ts';
	import { onMount } from 'svelte';

	let sock: WS;
	onMount(() => {
		// Replace port 8080 with the port of the backend
		try {
			sock = new WebSocket('ws://localhost:8080/remote/ws/');

			sock.addEventListener('open', () => {
				console.log('Opened');
			});

            sock.addEventListener('close', () => {
				console.log('Closed');
			});

            sock.addEventListener('error', () => {
                console.error();
            });

            sock.onmessage = function(event: MessageEvent) {
          const data = event.data;

          console.log("data received: %s", data);
        };
		} catch {
			console.log('ws refused connection\n');
		}
		console.log('the component has mounted');
	});
</script>

<h1 style="text-align: center;">U-Peeper Remote</h1>
<div class="grid">
	<div class="div1">
		<RemoteButton socket={sock} cmd={CMD_Types.FORWARD} />
	</div>
	<div class="div2">
		<RemoteButton socket={sock} cmd={CMD_Types.LEFT} />
	</div>
	<div class="div3">
		<RemoteButton socket={sock} cmd={CMD_Types.RIGHT} />
	</div>
	<div class="div4">
		<RemoteButton socket={sock} cmd={CMD_Types.BACK} />
	</div>
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		grid-template-rows: repeat(5, 1fr);
		grid-column-gap: 0px;
		grid-row-gap: 0px;
	}

	.div1 {
		grid-area: 2 / 3 / 3 / 4;
	}
	.div2 {
		grid-area: 3 / 2 / 4 / 3;
	}
	.div3 {
		grid-area: 3 / 4 / 4 / 5;
	}
	.div4 {
		grid-area: 4 / 3 / 5 / 4;
	}
</style>
