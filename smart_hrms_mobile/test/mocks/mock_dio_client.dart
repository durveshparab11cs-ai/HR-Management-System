import 'package:dio/dio.dart';
import 'package:mockito/mockito.dart';

/// Mock HTTP client for testing
class MockDioClient extends Mock implements Dio {
  @override
  Future<Response<T>> get<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onReceiveProgress,
  }) async {
    return super.noSuchMethod(
      Invocation.method(
        #get,
        [path],
        {
          #queryParameters: queryParameters,
          #options: options,
        },
      ),
      returnValue: Future<Response<T>>.value(
        Response<T>(
          data: {} as T,
          statusCode: 200,
          requestOptions: RequestOptions(path: path),
        ),
      ),
    ) as Future<Response<T>>;
  }

  @override
  Future<Response<T>> post<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    return super.noSuchMethod(
      Invocation.method(
        #post,
        [path],
        {
          #data: data,
          #queryParameters: queryParameters,
          #options: options,
        },
      ),
      returnValue: Future<Response<T>>.value(
        Response<T>(
          data: {} as T,
          statusCode: 200,
          requestOptions: RequestOptions(path: path),
        ),
      ),
    ) as Future<Response<T>>;
  }

  @override
  Future<Response<T>> put<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    return super.noSuchMethod(
      Invocation.method(
        #put,
        [path],
        {
          #data: data,
          #queryParameters: queryParameters,
          #options: options,
        },
      ),
      returnValue: Future<Response<T>>.value(
        Response<T>(
          data: {} as T,
          statusCode: 200,
          requestOptions: RequestOptions(path: path),
        ),
      ),
    ) as Future<Response<T>>;
  }

  @override
  Future<Response<T>> delete<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return super.noSuchMethod(
      Invocation.method(
        #delete,
        [path],
        {
          #data: data,
          #queryParameters: queryParameters,
          #options: options,
        },
      ),
      returnValue: Future<Response<T>>.value(
        Response<T>(
          data: {} as T,
          statusCode: 200,
          requestOptions: RequestOptions(path: path),
        ),
      ),
    ) as Future<Response<T>>;
  }
}
