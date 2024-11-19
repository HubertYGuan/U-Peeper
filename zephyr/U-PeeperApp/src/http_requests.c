#include <stdio.h>
#include <stdlib.h>
#include <zephyr/net/socket.h>
#include <zephyr/kernel.h>
#include "http_requests.h"

void nslookup(const char *hostname, struct zsock_addrinfo **results)
{
	struct zsock_addrinfo hints = {
		.ai_family = AF_INET, // Allow only IPv4 (mainly since it's easier)
		.ai_socktype = SOCK_STREAM,
	};
	int err = zsock_getaddrinfo(hostname, NULL, &hints, (struct zsock_addrinfo **)results);
	if (err) {
		printf("Failed to get addr info: %d", err);
	}
}

void PrintAddrInfoResults(struct zsock_addrinfo **results)
{
	char ipv4[INET_ADDRSTRLEN];
	struct sockaddr_in *sa;
	struct zsock_addrinfo *rp;

	for (rp = *results; rp != NULL; rp = rp->ai_next) {
		// IPv4 Addresses only
		sa = (struct sockaddr_in *)rp->ai_addr;
		zsock_inet_ntop(AF_INET, &sa->sin_addr, ipv4, INET_ADDRSTRLEN);
		printf("IPv4: %s\n", ipv4);
	}
}

int ConnectSocket(struct zsock_addrinfo **results, uint16_t port)
{
	int sock;
	int ret;
	struct zsock_addrinfo *rp;
	struct sockaddr_in *sa;

	// Create IPv4 Socket
	sock = zsock_socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	if (sock < 0) {
		printk("Error creating IPv4 socket\n");
		return (-1);
	}

	// Iterate through IPv4 addresses until we get a successful connection
	for (rp = *results; rp != NULL; rp = rp->ai_next) {
		if (rp->ai_addr->sa_family == AF_INET) {
			// IPv4 Address
			sa = (struct sockaddr_in *)rp->ai_addr;
			sa->sin_port = htons(port);

			char ipv4[INET_ADDRSTRLEN];
			zsock_inet_ntop(AF_INET, &sa->sin_addr, ipv4, INET_ADDRSTRLEN);
			printk("Connecting to %s:%d ", ipv4, port);

			ret = zsock_connect(sock, (struct sockaddr *)sa,
					    sizeof(struct sockaddr_in));
			if (ret == 0) {
				printk("Success\r\n");
				return (sock);
			} else {
				printk("Failure (%d)\r\n", ret);
			}
		}
	}
	return 0;
}

static void http_response_cb(struct http_response *rsp, enum http_final_call final_data,
			     void *user_data)
{
	// Might need to store the data in heap idk but heap bad
	printk("HTTP Response Callback: %.*s", rsp->data_len, rsp->recv_buf);
}

int HTTPRequest(int sock, char *hostname, char *url, enum http_method method)
{
	struct http_request req = {0};
	static uint8_t recv_buf[512];
	int ret;

	req.method = method;
	req.url = url;
	req.host = hostname;
	req.protocol = "HTTP/1.1";
	req.response = http_response_cb;
	req.recv_buf = recv_buf;
	req.recv_buf_len = sizeof(recv_buf);

	ret = http_client_req(sock, &req, 5000, NULL);
	return ret;
}