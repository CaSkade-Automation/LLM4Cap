package clients.gpt;

public class CompletionChoice {

	/**
	 * This index of this completion in the returned list.
	 */
	Integer index;
	
	/**
	 * The generated message
	 */
	Message message;

	/**
	 * The reason why GPT stopped generating, for example "length".
	 */
	String finish_reason;
	
	public Integer getIndex() {
		return this.index;
	}

	public Message getMessage() {
		return message;
	}

	public String getFinish_reason() {
		return finish_reason;
	}
}