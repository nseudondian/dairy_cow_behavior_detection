import { responseApi } from 'use-hook-api';

// export const getVideosApi = () => {
//     return responseApi(`/video_information`, 'get', null);
// };
export const getVideosApi = () => {
    return responseApi(`/get_all_videos`, 'get', null);
  }
  

export const uploadVideoApi = (payload: any) => {
    return responseApi(`/upload`, 'post', payload);
}

export const inferenceVideoApi = (payload: any) => {
    return responseApi(`/start_inference`, 'post', payload);
}