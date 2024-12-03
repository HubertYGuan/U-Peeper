<script lang="ts">
	import { CMD_Types } from '$lib/U-Peeper_WS.ts';

	import type { WebSocket } from 'ws';

	import { onMount, onDestroy } from 'svelte';

	let { socket, cmd }: { socket: WebSocket; cmd: number } = $props();

	let cmd_name = $state('ERROR');

	const stop_cmd = cmd + 4;
	let keyBinding = '';

	switch (cmd) {
		case CMD_Types.FORWARD:
			cmd_name = 'Forward';
			keyBinding = 'w';
			break;
		case CMD_Types.LEFT:
			cmd_name = 'Left';
			keyBinding = 'a';
			break;
		case CMD_Types.RIGHT:
			cmd_name = 'Right';
			keyBinding = 'd';
			break;
		case CMD_Types.BACK:
			cmd_name = 'Back';
			keyBinding = 's';
			break;
		default:
			break;
	}

	let sending: Boolean = false;

	function start() {
		const arr = new Uint8Array(1);
		arr[0] = cmd;
		socket.send(arr);
		console.log('starting button');
		sending = true;
	}

	function stop() {
		if (!sending) {
			return;
		}
		sending = false;
		const arr = new Uint8Array(1);
		arr[0] = stop_cmd;
		socket.send(arr);
		console.log('stopping button');
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key.toLowerCase() === keyBinding && !sending) {
			start();
		}
	}

	function handleKeyUp(event: KeyboardEvent) {
		if (event.key.toLowerCase() === keyBinding) {
			stop();
		}
	}

	onMount(() => {
		window.addEventListener('keydown', handleKeyDown);
		window.addEventListener('keyup', handleKeyUp);
	});

	const buttonClass =
		cmd === CMD_Types.FORWARD
			? 'forward'
			: cmd === CMD_Types.LEFT
				? 'left'
				: cmd === CMD_Types.RIGHT
					? 'right'
					: cmd === CMD_Types.BACK
						? 'back'
						: '';
</script>

<button class={buttonClass} onpointerdown={start} onpointerup={stop} onpointerleave={stop}>
	{cmd_name}
</button>

<style>
	button {
		--pico-font-weight: 700;
		border-left: 20px solid transparent;
		border-right: 20px solid transparent;
		border-bottom: 30px solid black; /* Default to pointing down */
		display: inline-block;
		touch-action: none;
	}

	.forward {
		transform: rotate(0deg);
	}

	.left {
		transform: rotate(-90deg);
	}

	.right {
		transform: rotate(90deg);
	}

	.back {
		transform: rotate(180deg);
	}
</style>
