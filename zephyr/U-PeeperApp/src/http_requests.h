/**
 * @file http_requests.h
 * @brief HTTP request and socket management header file
 *
 */

#ifndef HTTP_REQUESTS_H
#include <stdio.h>
#include <stdlib.h>
#include <zephyr/net/http/client.h>
#include <zephyr/net/socket.h>

/**
 * @brief Prints IPv4 addresses after IP query
 * @param results: zsock_addrinfo array pointer used to store IP query results
 */
void PrintAddrInfoResults(struct zsock_addrinfo **results);

/**
 * @brief Makes an HTTP request
 *
 * @param sock: Socket file descriptor
 * @param hostname: Host IP Address and port
 * @param url: Path to endpoint after hostname
 * @param method: HTTP method
 * @return int: <0 if error, else number of bytes sent to the server
 */
int HTTPRequest(int sock, char *hostname, char *url, enum http_method method);

/**
 * @brief Makes a socket connection after IP query
 *
 * @param results: zsock_addrinfo array pointer used to store IP query results
 * @param port: Host port
 * @return int: <0 if error, else socket file descriptor
 */
int ConnectSocket(struct zsock_addrinfo **results, uint16_t port);

#endif // !HTTP_REQUESTS_H
