// Enhanced ViewModel for PersonAI
class PersonAIViewModel : ViewModel() {
    private val repository = PersonAIRepository()
    private val _personData = MutableLiveData<State<Person>>()
    val personData: LiveData<State<Person>> get() = _personData

    fun fetchPersonData() {
        _personData.value = State.Loading
        viewModelScope.launch {
            try {
                val data = repository.getPersonData()
                _personData.value = State.Success(data)
            } catch (e: Exception) {
                _personData.value = State.Error(e.message)
            }
        }
    }
}