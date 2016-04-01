#
# encoding: utf-8

from tornado.concurrent import Future


def mkfuture(result):
    future = Future()
    future.set_result(result)
    return future


def mkfuture_exception(exception):
    future = Future()
    future.set_exception(exception)
    return future
