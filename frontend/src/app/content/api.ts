import api from "@/utils/api";

interface ContentBody {
  content_title: string;
  content_text: string;
  content_metadata: Record<string, unknown>;
}
const getContentList = async ({
  token,
  skip = 0,
  limit = 200,
}: {
  token: string;
  skip?: number;
  limit?: number;
}) => {
  try {
    const response = await api.get(`/content/?skip=${skip}&limit=${limit}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching content list");
  }
};

const getContent = async (content_id: number, token: string) => {
  try {
    const response = await api.get(`/content/${content_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error fetching content");
  }
};

const deleteContent = async (content_id: number, token: string) => {
  try {
    const response = await api.delete(`/content/${content_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    throw new Error("Error deleting content");
  }
};


export {
  getContentList,
  getContent,
  deleteContent,
};
