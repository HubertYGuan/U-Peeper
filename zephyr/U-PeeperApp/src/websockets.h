/**
 * @file websockets.h
 * @brief WebSocket connection management header file
 *
 */

#ifndef WEBSOCKETS_H
#define WEBSOCKETS_H 6.9

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(net_websocket_client_sample, LOG_LEVEL_DBG);

#include <zephyr/misc/lorem_ipsum.h>
#include <zephyr/net/net_ip.h>
#include <zephyr/net/socket.h>
#include <zephyr/net/websocket.h>
#include <zephyr/random/random.h>
#include <zephyr/shell/shell.h>
#include "wifi_settings.h"

#define SERVER_ADDR4 BACKEND_HOST

#define MAX_RECV_BUF_LEN 696

/* We need to allocate bigger buffer for the websocket data we receive so that
 * the websocket header fits into it.
 */
#define EXTRA_BUF_SPACE 30

uint8_t temp_recv_buf_ipv4[MAX_RECV_BUF_LEN + EXTRA_BUF_SPACE];

int connect_cb(int sock, struct http_request *req, void *user_data)
{
	printk("Websocket %d for %s connected.", sock, (char *)user_data);

	return 0;
}

size_t how_much_to_send(size_t max_len)
{
	size_t amount;

	do {
		amount = sys_rand32_get() % max_len;
	} while (amount == 0U);

	return amount;
}

/**
 * @brief Send data across WebSocket connection
 *
 * @param sock: WebSocket file descriptor
 * @param buf: Buffer to send from
 * @param len: Length of message (obviously in bytes)
 * @return ssize_t: <0 if error, else the number of bytes sent
 */
ssize_t sendall_ws(int sock, const void *buf, size_t len)
{
	return websocket_send_msg(sock, buf, len, WEBSOCKET_OPCODE_DATA_TEXT, true, true,
				  SYS_FOREVER_MS);
}

/**
 * @brief Receive data over WebSocket connection
 *
 * @param sock: WebSocket file descriptor
 * @param amount: Amount of data to receive
 * @param buf: Buffer to write to
 * @param buf_len: Length of buffer
 * @param proto: Network protocol (usu. "IPv4")
 * @return int: <0 if error, else number of bytes received
 */
int recv_data_ws(int sock, size_t amount, uint8_t *buf, size_t buf_len, const char *proto)
{
	uint64_t remaining = ULLONG_MAX;
	int total_read;
	uint32_t message_type;
	int ret, read_pos;

	ret = -1;
	read_pos = 0;
	total_read = 0;

	while (remaining > 0) {
		ret = websocket_recv_msg(sock, buf + read_pos, buf_len - read_pos, &message_type,
					 &remaining, 0);
		if (ret < 0) {
			if (ret == -EAGAIN) {
				k_sleep(K_MSEC(50));
				continue;
			}

			printk("%s connection closed while "
			       "waiting (%d/%d)",
			       proto, ret, errno);
			break;
		}

		read_pos += ret;
		total_read += ret;
	}

	return ret;
}

#endif // !WEBSOCKETS_H
