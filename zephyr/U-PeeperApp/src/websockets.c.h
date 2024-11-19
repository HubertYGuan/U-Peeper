/*
 * Copyright (c) 2019 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "websockets.h"
#include "wifi_settings.h"

int setup_socket(sa_family_t family, const char *server, int port, int *sock, struct sockaddr *addr,
		 socklen_t addr_len)
{
	const char *family_str = "IPv4";
	int ret = 0;

	memset(addr, 0, addr_len);

	net_sin(addr)->sin_family = AF_INET;
	net_sin(addr)->sin_port = htons(port);
	inet_pton(family, server, &net_sin(addr)->sin_addr);

	*sock = socket(family, SOCK_STREAM, IPPROTO_TCP);

	if (*sock < 0) {
		LOG_ERR("Failed to create %s HTTP socket (%d)", family_str, -errno);
	}

	return ret;
}

int connect_socket(sa_family_t family, const char *server, int port, int *sock,
		   struct sockaddr *addr, socklen_t addr_len)
{
	int ret;

	ret = setup_socket(family, server, port, sock, addr, addr_len);
	if (ret < 0 || *sock < 0) {
		return -1;
	}

	ret = connect(*sock, addr, addr_len);
	if (ret < 0) {
		LOG_ERR("Cannot connect to %s remote (%d)", "IPv4", -errno);
		ret = -errno;
	}

	return ret;
}

int connect_cb(int sock, struct http_request *req, void *user_data)
{
	LOG_INF("Websocket %d for %s connected.", sock, (char *)user_data);

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

ssize_t sendall_with_ws_api(int sock, const void *buf, size_t len)
{
	return websocket_send_msg(sock, buf, len, WEBSOCKET_OPCODE_DATA_TEXT, true, true,
				  SYS_FOREVER_MS);
}

void recv_data_ws_api(int sock, size_t amount, uint8_t *buf, size_t buf_len, const char *proto)
{
	uint64_t remaining = ULLONG_MAX;
	int total_read;
	uint32_t message_type;
	int ret, read_pos;

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

			LOG_DBG("%s connection closed while "
				"waiting (%d/%d)",
				proto, ret, errno);
			break;
		}

		read_pos += ret;
		total_read += ret;
	}

	if (remaining != 0 || total_read != amount ||
	    /* Do not check the final \n at the end of the msg */
	    memcmp(lorem_ipsum, buf, amount - 1) != 0) {
		LOG_ERR("%s data recv failure %zd/%d bytes (remaining %" PRId64 ")", proto, amount,
			total_read, remaining);
		LOG_HEXDUMP_DBG(buf, total_read, "received ws buf");
		LOG_HEXDUMP_DBG(lorem_ipsum, total_read, "sent ws buf");
	} else {
		LOG_DBG("%s recv %d bytes", proto, total_read);
	}
}

bool send_and_wait_msg(int sock, size_t amount, const char *proto, uint8_t *buf, size_t buf_len)
{
	static int count;
	int ret;

	if (sock < 0) {
		return true;
	}

	/* Terminate the sent data with \n so that we can use the
	 *      websocketd --port=9001 cat
	 * command in server side.
	 */
	memcpy(buf, lorem_ipsum, amount);
	buf[amount] = '\n';

	ret = sendall_with_ws_api(sock, buf, amount + 1);

	if (ret <= 0) {
		if (ret < 0) {
			LOG_ERR("%s failed to send data using %s (%d)", proto,
				(count % 2) ? "ws API" : "socket API", ret);
		} else {
			LOG_DBG("%s connection closed", proto);
		}

		return false;
	} else {
		LOG_DBG("%s sent %d bytes", proto, ret);
	}

	recv_data_ws_api(sock, amount + 1, buf, buf_len, proto);

	count++;

	return true;
}

static int sample_main(void)
{
	/* Just an example how to set extra headers */
	const char *extra_headers[] = {"Origin: http://foobar\r\n", NULL};
	int sock4 = -1;
	int websock4 = -1;
	int32_t timeout = 3 * MSEC_PER_SEC;
	struct sockaddr_in addr4;
	size_t amount;
	int ret;

	(void)connect_socket(AF_INET, SERVER_ADDR4, SERVER_PORT, &sock4, (struct sockaddr *)&addr4,
			     sizeof(addr4));

	if (sock4 < 0) {
		LOG_ERR("Cannot create HTTP connection.");
		k_sleep(K_FOREVER);
	}

	struct websocket_request req;

	memset(&req, 0, sizeof(req));

	req.host = SERVER_ADDR4;
	req.url = "/ws/";
	req.optional_headers = extra_headers;
	req.cb = connect_cb;
	req.tmp_buf = temp_recv_buf_ipv4;
	req.tmp_buf_len = sizeof(temp_recv_buf_ipv4);

	websock4 = websocket_connect(sock4, &req, timeout, "IPv4");
	if (websock4 < 0) {
		LOG_ERR("Cannot connect to %s:%d", SERVER_ADDR4, SERVER_PORT);
		close(sock4);
	}

	if (websock4 < 0) {
		LOG_ERR("No IPv4 connectivity");
		k_sleep(K_FOREVER);
	}

	LOG_INF("Websocket IPv4 %d", websock4);

	while (1) {
		amount = how_much_to_send(ipsum_len);

		if (websock4 >= 0 && !send_and_wait_msg(websock4, amount, "IPv4", recv_buf_ipv4,
							sizeof(recv_buf_ipv4))) {
			break;
		}

		k_sleep(K_MSEC(250));
	}

	if (websock4 >= 0) {
		close(websock4);
	}

	if (sock4 >= 0) {
		close(sock4);
	}

	k_sleep(K_FOREVER);
	return 0;
}
