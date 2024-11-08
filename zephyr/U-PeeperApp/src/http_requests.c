#include <stdio.h>
#include <stdlib.h>
#include <zephyr/net/socket.h>
#include <zephyr/kernel.h>
#include <zephyr/net/http/client.h>
#include "http_requests.h"

void nslookup(const char *hostname, zsock_addrinfo **results)
{
    struct zsock_addrinfo hints = {
		.ai_family = AF_UNSPEC,		// Allow IPv4 or IPv6	
		.ai_socktype = SOCK_STREAM,
	};
    int err = zsock_getaddrinfo(hostname, NULL, &hints, (struct zsock_addrinfo **) results);
    if (err)
    {
        printf("Failed to get addr info: %d", err);
    }
}

int ConnectSocket(zsock_addrinfo **results, uint16_t port)
{
	return 0;
}
