#ifndef HTTP_REQUESTS_H
#include <stdio.h>
#include <stdlib.h>
#include <zephyr/net/http/client.h>
#include <zephyr/net/socket.h>

void PrintAddrInfoResults(struct zsock_addrinfo **results);
int HTTPRequest(int sock, char * hostname, char * url, enum http_method method);

int ConnectSocket(struct zsock_addrinfo **results, uint16_t port);

#endif // !HTTP_REQUESTS_H

