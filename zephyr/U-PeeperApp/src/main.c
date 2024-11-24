/*
 * Copyright (c) 2023 Craig Peacock.
 * Copyright (c) 2017 ARM Ltd.
 * Copyright (c) 2016 Intel Corporation.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/*
 * Craig Peacock's original code actually doesn't compile on current Zephyr
 * So this is modified to hopefully keep the same functionality while being compilable
 */

#include <zephyr/kernel.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/net/net_event.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include "websockets.h"
#include "ping.h"
#include "http_requests.h"

static K_SEM_DEFINE(wifi_connected, 0, 1);
static K_SEM_DEFINE(ipv4_address_obtained, 0, 1);

static struct net_mgmt_event_callback wifi_cb;
static struct net_mgmt_event_callback ipv4_cb;

static void handle_wifi_connect_result(struct net_mgmt_event_callback *cb)
{
	const struct wifi_status *status = (const struct wifi_status *)cb->info;

	if (status->status) {
		printk("Connection request failed (%d)\n", status->status);
	} else {
		printk("Connected\n");
		k_sem_give(&wifi_connected);
	}
}

static void handle_wifi_disconnect_result(struct net_mgmt_event_callback *cb)
{
	const struct wifi_status *status = (const struct wifi_status *)cb->info;

	if (status->status) {
		printk("Disconnection request (%d)\n", status->status);
	} else {
		printk("Disconnected\n");
	}
}

static void handle_ipv4_result(struct net_if *iface)
{
	int i = 0;

	for (i = 0; i < NET_IF_MAX_IPV4_ADDR; i++) {

		char buf[NET_IPV4_ADDR_LEN];

		if (iface->config.ip.ipv4->unicast[i].ipv4.addr_type != NET_ADDR_DHCP) {
			continue;
		}

		printk("IPv4 address: %s\n",
		       net_addr_ntop(AF_INET,
				     &iface->config.ip.ipv4->unicast[i].ipv4.address.in_addr, buf,
				     sizeof(buf)));
		printk("Subnet: %s\n",
		       net_addr_ntop(AF_INET, &iface->config.ip.ipv4->unicast[i].netmask, buf,
				     sizeof(buf)));
		printk("Router: %s\n",
		       net_addr_ntop(AF_INET, &iface->config.ip.ipv4->gw, buf, sizeof(buf)));
	}

	k_sem_give(&ipv4_address_obtained);
}

static void wifi_mgmt_event_handler(struct net_mgmt_event_callback *cb, uint32_t mgmt_event,
				    struct net_if *iface)
{
	switch (mgmt_event) {

	case NET_EVENT_WIFI_CONNECT_RESULT:
		handle_wifi_connect_result(cb);
		break;

	case NET_EVENT_WIFI_DISCONNECT_RESULT:
		handle_wifi_disconnect_result(cb);
		break;

	case NET_EVENT_IPV4_ADDR_ADD:
		handle_ipv4_result(iface);
		break;

	default:
		break;
	}
}

// No Security network (you may have to change the security to PSK and include the psk)
void wifi_connect(void)
{
	struct net_if *iface = net_if_get_default();

	struct wifi_connect_req_params wifi_params = {0};

	wifi_params.ssid = SSID;
	wifi_params.ssid_length = strlen(SSID);
	wifi_params.channel = WIFI_CHANNEL_ANY;
	wifi_params.security = WIFI_SECURITY_TYPE_NONE;
	wifi_params.band = WIFI_FREQ_BAND_2_4_GHZ;
	wifi_params.mfp = WIFI_MFP_OPTIONAL;

	printk("Connecting to SSID: %s\n", wifi_params.ssid);

	if (net_mgmt(NET_REQUEST_WIFI_CONNECT, iface, &wifi_params,
		     sizeof(struct wifi_connect_req_params))) {
		printk("WiFi Connection Request Failed\n");
	} else {
		printk("Connected successfully\n");
	}
}

void wifi_status(void)
{
	struct net_if *iface = net_if_get_default();

	struct wifi_iface_status status = {0};

	if (net_mgmt(NET_REQUEST_WIFI_IFACE_STATUS, iface, &status,
		     sizeof(struct wifi_iface_status))) {
		printk("WiFi Status Request Failed\n");
	}

	if (status.state >= WIFI_STATE_ASSOCIATED) {
		printk("SSID: %-32s\n", status.ssid);
		printk("Band: %s\n", wifi_band_txt(status.band));
		printk("Channel: %d\n", status.channel);
		printk("Security: %s\n", wifi_security_txt(status.security));
		printk("RSSI: %d\n", status.rssi);
	}
}

void wifi_disconnect(void)
{
	struct net_if *iface = net_if_get_default();

	if (net_mgmt(NET_REQUEST_WIFI_DISCONNECT, iface, NULL, 0)) {
		printk("WiFi Disconnection Request Failed\n");
	}
}

// returns the socket fd and -1 upon fail
int connect_and_get_socket(void)
{
	printk("U-Peeper WiFi App\nBoard: %s\n", CONFIG_BOARD);

	net_mgmt_init_event_callback(&wifi_cb, wifi_mgmt_event_handler,
				     NET_EVENT_WIFI_CONNECT_RESULT |
					     NET_EVENT_WIFI_DISCONNECT_RESULT);

	net_mgmt_init_event_callback(&ipv4_cb, wifi_mgmt_event_handler, NET_EVENT_IPV4_ADDR_ADD);

	net_mgmt_add_event_callback(&wifi_cb);
	net_mgmt_add_event_callback(&ipv4_cb);

	wifi_connect();
	k_sem_take(&wifi_connected, K_FOREVER);
	wifi_status();
	k_sem_take(&ipv4_address_obtained, K_FOREVER);
	printk("Ready...\n\n");

	printk("\nLooking up IP addresses:\n");

	struct zsock_addrinfo *res;
	int st, sock = -1;
	static struct zsock_addrinfo hints;
	/*
	 * struct sock_addr s_addr;
	 * res->ai_addr = &s_addr;
	 */

	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_STREAM;

	st = zsock_getaddrinfo(BACKEND_HOST, BACKEND_PORT, &hints, &res);
	if (st) {
		printf("Unable to resolve address, quitting\n");

		k_sleep(K_SECONDS(5));
		wifi_disconnect();
		// Error codes aren't really supported right now
		return 0;
	}

	PrintAddrInfoResults(&res);

	printk("bConnecting to HTTP Server:\n");
	sock = ConnectSocket(&res, 8080);

	int httpret = HTTPRequest(sock, BACKEND_HOST, "/", HTTP_GET);
	if (httpret < 0) {
		zsock_close(sock);

		wifi_disconnect();
		return -1;
	}
	return sock;
}

// returns websocket fd
int connect_websocket(int sock)
{
	int websock = -1;
	int32_t timeout = 3 * MSEC_PER_SEC;
	// struct sockaddr_in addr4;

	printk("\nConnecting to HTTP Server:\n");

	struct websocket_request req;

	memset(&req, 0, sizeof(req));

	req.host = BACKEND_HOST;
	req.url = "/ws/";
	req.cb = connect_cb;
	req.tmp_buf = temp_recv_buf_ipv4;
	req.tmp_buf_len = sizeof(temp_recv_buf_ipv4);

	websock = websocket_connect(sock, &req, timeout, "IPv4");
	if (websock < 0) {
		printk("Cannot connect to %s:%d", BACKEND_HOST, 8080);
		return websock;
	}

	printk("Websocket IPv4 %d", websock);
	return websock;
}

int main(void)
{
	// NASA would be pissed that I don't have max iterations on these loops
	int sock = -1;
	do {
		k_sleep(K_SECONDS(1));
		sock = connect_and_get_socket();
	} while (sock < 0);

	int websock = -1;
	do {
		k_sleep(K_SECONDS(1));
		sock = connect_websocket(sock);
	} while (sock < 0);
	size_t amount;
	int retries = 0;
	while (retries < 10) {
		printk("Sending Lorem Message");
		amount = how_much_to_send(ipsum_len);

		if (websock >= 0 && !send_and_wait_msg(websock, amount, "IPv4", recv_buf_ipv4,
						       sizeof(recv_buf_ipv4))) {
			break;
		}

		k_sleep(K_MSEC(250));
		retries++;
	}
}